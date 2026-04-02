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
        "critique", help="Critique a single image (no generator needed)",
    )
    crit_parser.add_argument("image", help="Path to the image file.")
    crit_parser.add_argument(
        "--critic", default="wolfflin",
        help="Critic card name or path (default: wolfflin).",
    )
    crit_parser.add_argument(
        "--model", default="openai:gpt-4o",
        help="LLM model string (default: openai:gpt-4o).",
    )
    crit_parser.add_argument("--intent", help="Project intent for the critic to factor in.")
    crit_parser.set_defaults(func=cmd_critique)

    # --- run ---
    run_parser = subparsers.add_parser("run", help="Run the improvement loop with a generator")
    run_parser.add_argument(
        "--critic", default="wolfflin",
        help="Critic card name or path (default: wolfflin).",
    )
    run_parser.add_argument(
        "--generator", default="rewriter",
        help="Generator adapter (default: rewriter). See adapters/ for available generators.",
    )
    run_parser.add_argument(
        "--model", default="openai:gpt-4o",
        help="LLM model string (default: openai:gpt-4o).",
    )
    run_parser.add_argument("--iterations", type=int, default=10, help="Max iterations (default: 10).")
    run_parser.add_argument("--intent", help="Project intent for the critic.")
    run_parser.add_argument("--server-url", default="http://127.0.0.1:8010", help="Generator server URL.")
    run_parser.add_argument("--output-dir", default="runs", help="Output directory (default: runs/).")
    run_parser.add_argument("--damping", type=float, default=0.7, help="Delta damping 0-1 (default: 0.7).")
    run_parser.add_argument("--random-seed", type=int, default=None, help="Random seed (default: random).")
    run_parser.add_argument("--frames", type=int, default=24, help="Growth steps per simulation (default: 24).")
    run_parser.add_argument("--events-per-frame", type=int, default=30, help="Events per step (default: 30).")
    run_parser.set_defaults(func=cmd_run)

    # --- validate ---
    val_parser = subparsers.add_parser("validate", help="Validate critic card JSON files")
    val_parser.add_argument("cards", nargs="+", help="Paths to critic card JSON files.")
    val_parser.set_defaults(func=cmd_validate)

    # --- list ---
    list_parser = subparsers.add_parser("list", help="List available critic cards")
    list_parser.set_defaults(func=cmd_list)

    # --- report ---
    report_parser = subparsers.add_parser("report", help="Generate contact sheet for an existing run")
    report_parser.add_argument("run_dir", help="Path to the run directory.")
    report_parser.set_defaults(func=cmd_report)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
