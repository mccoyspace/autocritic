"""
CLI entry point for autocritic.

Usage:
    python3 -m autocritic critique image.png --critic wolfflin --model openai:gpt-4o
    python3 -m autocritic run --critic wolfflin --generator rewriter --iterations 5
    python3 -m autocritic validate critics/*.json
    python3 -m autocritic report runs/rewriter_123456/
    python3 -m autocritic list
"""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _bundled_critics_dir() -> Path:
    """Return the path to bundled critic cards inside the installed package."""
    return Path(__file__).resolve().parent / "critics"


def _resolve_critic(name: str) -> Path:
    """Resolve a critic card name or path to a Path, or exit.

    Search order:
      1. CWD-relative ``critics/<name>.json``
      2. Bundled package data ``autocritic/critics/<name>.json``
      3. Literal path (``<name>`` as given)
    """
    # 1. CWD
    card_path = Path(f"critics/{name}.json")
    if card_path.exists():
        return card_path

    # 2. Bundled with the package
    pkg_path = _bundled_critics_dir() / f"{name}.json"
    if pkg_path.exists():
        return pkg_path

    # 3. Literal path
    card_path = Path(name)
    if card_path.exists():
        return card_path

    print(f"Error: critic card not found: {name}")
    for search_dir in [Path("critics"), _bundled_critics_dir()]:
        try:
            available = ", ".join(p.stem for p in search_dir.glob("*.json"))
            if available:
                print(f"Available: {available}")
                break
        except Exception:
            continue
    sys.exit(1)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_critique(args: argparse.Namespace) -> None:
    """Critique a single image — no generator needed."""
    from autocritic.critic import load_critic
    from autocritic.scoring import ScoreParseError, score_critique

    card_path = _resolve_critic(args.critic)
    image_path = Path(args.image)
    if not image_path.exists():
        print(f"Error: image not found: {image_path}")
        sys.exit(1)

    critic = load_critic(card_path)
    print(f"Critiquing {image_path.name} through {critic.label}...")
    print(f"Model: {args.model}\n")

    try:
        scored = score_critique(critic, image_path, model=args.model, intent=args.intent)
    except ScoreParseError as e:
        print(f"Error: could not parse axis scores from model response: {e}")
        sys.exit(1)

    print(f"Composite score: {scored.composite_score:.3f}\n")
    print("Axis scores:")
    for s in scored.axis_scores:
        print(f"  {s.label}: {s.score:.2f}")
        print(f"    {s.reasoning}\n")

    print("Lens summary:")
    print(f"  {scored.critique.lens_summary}\n")

    if scored.critique.strengths:
        print("Strengths:")
        for s in scored.critique.strengths:
            print(f"  + {s}")

    if scored.critique.weaknesses:
        print("\nWeaknesses:")
        for w in scored.critique.weaknesses:
            print(f"  - {w}")

    if scored.critique.directives:
        print("\nDirectives:")
        for d in scored.critique.directives:
            print(f"  > {d}")


def cmd_validate(args: argparse.Namespace) -> None:
    """Validate one or more critic card JSON files."""
    from autocritic.validate import main as validate_main
    raise SystemExit(validate_main(args.cards))


def cmd_list(args: argparse.Namespace) -> None:
    """List available critic cards."""
    # Search CWD first, fall back to bundled
    critics_dir = Path("critics")
    if not critics_dir.exists() or not list(critics_dir.glob("*.json")):
        critics_dir = _bundled_critics_dir()
    if not critics_dir.exists():
        print("No critic cards found.")
        return

    from autocritic.critic import load_critic
    cards = sorted(critics_dir.glob("*.json"))
    if not cards:
        print("No critic cards found.")
        return

    print(f"{'ID':<14} {'Theorist':<24} {'Book':<36} {'Items'}")
    print("-" * 90)
    for card_path in cards:
        try:
            critic = load_critic(card_path)
            n_total = len(critic.items) + sum(len(v) for v in critic.secondary_items.values())
            items_desc = f"{n_total} {critic.items_key}"
            if critic.secondary_items:
                items_desc += f" (+{', '.join(critic.secondary_items.keys())})"
            print(f"{critic.critic_id:<14} {critic.theorist:<24} {critic.book:<36} {items_desc}")
        except Exception as e:
            print(f"{card_path.stem:<14} ERROR: {e}")


def cmd_eval(args: argparse.Namespace) -> None:
    """Run evaluation suites against critic cards."""
    from evals.runner import run_programmatic_suite, save_results, print_summary

    suite = args.suite
    critic = args.critic if args.critic != "all" else None
    any_failed = False

    if suite in ("programmatic", "all"):
        run_result = run_programmatic_suite(critic_filter=critic)
        print_summary(run_result)
        if not args.no_save:
            path = save_results(run_result)
            print(f"  Results saved to {path}\n")
        if run_result.failed > 0:
            any_failed = True

    if suite in ("usefulness", "all"):
        from evals.usefulness import run_usefulness_suite

        run_result = run_usefulness_suite(
            critic_filter=critic,
            model=args.model,
            refresh=args.refresh,
            include_judge=args.judge,
        )
        print_summary(run_result)
        if not args.no_save:
            path = save_results(run_result)
            print(f"  Results saved to {path}\n")
        if run_result.failed > 0:
            any_failed = True

    if suite == "fidelity":
        print("Suite 'fidelity' not yet implemented.")
        print("Available suites: programmatic, usefulness, all")
        sys.exit(1)

    if any_failed:
        sys.exit(1)


def cmd_report(args: argparse.Namespace) -> None:
    """Generate a contact sheet and narrative for an existing run."""
    from autocritic.report import generate_contact_sheet, save_narrative_md
    run_dir = Path(args.run_dir)
    if not (run_dir / "summary.json").exists():
        print(f"Error: no summary.json in {run_dir}")
        sys.exit(1)

    sheet = generate_contact_sheet(run_dir)
    md = save_narrative_md(run_dir)
    print(f"Contact sheet: {sheet}")
    print(f"Narrative: {md}")


def cmd_run(args: argparse.Namespace) -> None:
    """Run the critic-driven improvement loop with a generator."""
    card_path = _resolve_critic(args.critic)

    if args.generator == "rewriter":
        _run_rewriter(args, card_path)
    else:
        print(f"Error: unknown generator '{args.generator}'")
        print("Available generators: rewriter")
        print("\nTo add a generator, implement a ParamSpace and acquire_image function.")
        print("See src/autocritic/adapters/rewriter.py for an example.")
        sys.exit(1)


def _run_rewriter(args: argparse.Namespace, card_path: Path) -> None:
    """Run the loop with rewriteDrawer as the generator."""
    try:
        from autocritic.adapters.rewriter import (
            REWRITER_PARAM_SPACE,
            DEFAULT_REWRITER_PARAMS,
            acquire_image,
            check_server,
        )
    except ImportError:
        print("Error: rewriter adapter requires cairosvg.")
        print("Install with: pip install 'autocritic[rewriter]'")
        sys.exit(1)

    if not check_server(args.server_url):
        print(f"Error: rewriteDrawer server not reachable at {args.server_url}")
        print("Start it with: cd rewriteDrawer && python3 run_local.py")
        sys.exit(1)

    print(f"rewriteDrawer server OK at {args.server_url}")

    from autocritic.loop import LoopConfig, run_loop

    config = LoopConfig(
        critic_card_path=card_path,
        model=args.model,
        max_iterations=args.iterations,
        damping=args.damping,
        intent=args.intent,
        output_dir=Path(args.output_dir),
        generator_name="rewriter",
        generator_base_url=args.server_url,
    )

    initial_params = dict(DEFAULT_REWRITER_PARAMS)
    initial_params["random_seed"] = (
        args.random_seed if args.random_seed is not None
        else random.randint(0, 9999999)
    )
    initial_params["frames"] = args.frames
    initial_params["events_per_frame"] = args.events_per_frame

    print(f"Critic: {args.critic}")
    print(f"Model: {args.model}")
    print(f"Max iterations: {args.iterations}")
    print(f"Random seed: {initial_params['random_seed']}")
    print(f"Frames: {initial_params['frames']}")
    if args.intent:
        print(f"Intent: {args.intent}")

    def acquire(params, output_path):
        return acquire_image(params, output_path, base_url=args.server_url)

    result = run_loop(
        config=config,
        param_space=REWRITER_PARAM_SPACE,
        acquire_image_fn=acquire,
        initial_params=initial_params,
    )

    print(f"\nBest params:")
    for k, v in result.final_params.items():
        print(f"  {k}: {v}")


# ---------------------------------------------------------------------------
# Main parser
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="autocritic",
        description="Critic-card-driven image evaluation using art theory and LLMs.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # --- critique ---
    crit_parser = subparsers.add_parser(
        "critique",
        help="Critique a single image (no generator needed)",
        description=(
            "Evaluate a single image through a critic card's theoretical lens. "
            "Produces a qualitative critique with strengths, weaknesses, directives, "
            "and numeric axis scores. No generator or loop required.\n\n"
            "Examples:\n"
            "  autocritic critique photo.png --critic wolfflin\n"
            "  autocritic critique drawing.jpg --critic kandinsky --model openai:gpt-5.4\n"
            "  autocritic critique render.png --critic arnheim --intent 'organic branching'"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    crit_parser.add_argument("image", help="Path to the image file (PNG, JPG, etc.).")
    crit_parser.add_argument(
        "--critic", default="wolfflin",
        help="Critic card name or path. Use 'autocritic list' to see available cards (default: wolfflin).",
    )
    crit_parser.add_argument(
        "--model", default="openai:gpt-4o",
        help=(
            "LLM model string with provider prefix. "
            "Supported: openai:*, anthropic:*, google:*, xai:*, ollama:*, openrouter:* "
            "(default: openai:gpt-4o)."
        ),
    )
    crit_parser.add_argument(
        "--intent",
        help="Optional project intent (e.g. 'dense organic growth') for the critic to factor in.",
    )
    crit_parser.set_defaults(func=cmd_critique)

    # --- run ---
    run_parser = subparsers.add_parser(
        "run",
        help="Run the improvement loop with a generator",
        description=(
            "Run the critic-driven improvement loop: generate an image, critique it, "
            "translate the critique into parameter changes, and repeat. Requires a running "
            "generator server.\n\n"
            "Results (images, critiques, parameters, contact sheet) are saved to the output "
            "directory.\n\n"
            "Examples:\n"
            "  autocritic run --critic wolfflin --iterations 5\n"
            "  autocritic run --critic arnheim --intent 'organic branching' --damping 0.5\n"
            "  autocritic run --critic kandinsky --model openai:gpt-5.4 --frames 48"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    run_parser.add_argument(
        "--critic", default="wolfflin",
        help="Critic card name or path (default: wolfflin).",
    )
    run_parser.add_argument(
        "--generator", default="rewriter",
        help="Generator adapter (default: rewriter). See ADAPTERS.md for writing new adapters.",
    )
    run_parser.add_argument(
        "--model", default="openai:gpt-4o",
        help="LLM model string with provider prefix (default: openai:gpt-4o).",
    )
    run_parser.add_argument("--iterations", type=int, default=10, help="Max iterations (default: 10).")
    run_parser.add_argument("--intent", help="Project intent for the critic to factor in.")
    run_parser.add_argument("--server-url", default="http://127.0.0.1:8010", help="Generator server URL.")
    run_parser.add_argument("--output-dir", default="runs", help="Output directory (default: runs/).")
    run_parser.add_argument(
        "--damping", type=float, default=0.7,
        help="Delta damping factor 0-1. Lower = more conservative parameter changes (default: 0.7).",
    )
    run_parser.add_argument("--random-seed", type=int, default=None, help="Random seed for reproducibility (default: random).")
    run_parser.add_argument("--frames", type=int, default=24, help="Growth steps per simulation (default: 24).")
    run_parser.add_argument("--events-per-frame", type=int, default=30, help="Events per step (default: 30).")
    run_parser.set_defaults(func=cmd_run)

    # --- eval ---
    eval_parser = subparsers.add_parser(
        "eval",
        help="Run evaluation suites against critic cards",
        description=(
            "Run evaluation suites that measure critic card quality and critique usefulness.\n\n"
            "Suites:\n"
            "  programmatic  Structure, vocabulary, ground-truth checks (fast, no API key)\n"
            "  usefulness    Completeness, lens vocabulary, expected terms, coherence\n"
            "                (runs on cached critique fixtures; use --refresh to regenerate)\n"
            "  fidelity      Citation grounding and lens specificity (not yet implemented)\n"
            "  all           Run all available suites\n\n"
            "Results are saved as timestamped JSON in evals/results/.\n\n"
            "Examples:\n"
            "  autocritic eval                                    # programmatic checks, all critics\n"
            "  autocritic eval --suite usefulness                 # usefulness on cached fixtures\n"
            "  autocritic eval --suite usefulness --refresh       # regenerate fixtures first\n"
            "  autocritic eval --suite usefulness --judge         # include LLM-as-judge evals\n"
            "  autocritic eval --suite all --critic wolfflin      # all suites, one critic\n"
            "  autocritic eval --suite usefulness --model openai:gpt-5.4  # use specific model"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    eval_parser.add_argument(
        "--suite", default="programmatic",
        choices=["programmatic", "usefulness", "fidelity", "all"],
        help="Eval suite to run (default: programmatic).",
    )
    eval_parser.add_argument(
        "--critic", default="all",
        help="Critic card name or 'all' (default: all).",
    )
    eval_parser.add_argument(
        "--model", default="claude-sonnet-4-20250514",
        help="LLM model for fixture generation and judge evals (default: claude-sonnet-4-20250514).",
    )
    eval_parser.add_argument(
        "--no-save", action="store_true",
        help="Skip saving results to evals/results/.",
    )
    eval_parser.add_argument(
        "--refresh", action="store_true",
        help="Regenerate critique fixtures before evaluating (usefulness suite).",
    )
    eval_parser.add_argument(
        "--judge", action="store_true",
        help="Include LLM-as-judge evals: actionability and anti-generic checks (requires API key).",
    )
    eval_parser.set_defaults(func=cmd_eval)

    # --- validate ---
    val_parser = subparsers.add_parser(
        "validate",
        help="Validate critic card JSON files",
        description=(
            "Validate one or more critic card JSON files against the schema and runtime checks.\n\n"
            "Checks: JSON schema compliance, required fields, recognized ID fields on all items, "
            "snake_case ID patterns.\n\n"
            "Examples:\n"
            "  autocritic validate critics/wolfflin.json\n"
            "  autocritic validate critics/*.json"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    val_parser.add_argument("cards", nargs="+", help="Paths to critic card JSON files.")
    val_parser.set_defaults(func=cmd_validate)

    # --- list ---
    list_parser = subparsers.add_parser(
        "list",
        help="List available critic cards",
        description="List all available critic cards with their theorist, book, and item counts.",
    )
    list_parser.set_defaults(func=cmd_list)

    # --- report ---
    report_parser = subparsers.add_parser(
        "report",
        help="Generate contact sheet and narrative for an existing run",
        description=(
            "Generate a contact sheet (PNG image grid) and narrative summary (Markdown) "
            "for a completed improvement loop run.\n\n"
            "Example:\n"
            "  autocritic report runs/rewriter_1774718482/"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    report_parser.add_argument("run_dir", help="Path to the run directory (must contain summary.json).")
    report_parser.set_defaults(func=cmd_report)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
