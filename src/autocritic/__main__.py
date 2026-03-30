"""
CLI entry point for autocritic.

Usage:
    python3 -m autocritic run --critic wolfflin --iterations 5
    python3 -m autocritic validate critics/*.json
    python3 -m autocritic report runs/wolfram_123456/
    python3 -m autocritic list
"""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path


def cmd_validate(args: argparse.Namespace) -> None:
    """Validate one or more critic card JSON files."""
    from autocritic.validate import main as validate_main
    raise SystemExit(validate_main(args.cards))


def cmd_list(args: argparse.Namespace) -> None:
    """List available critic cards."""
    critics_dir = Path("critics")
    if not critics_dir.exists():
        print("No critics/ directory found.")
        return

    from autocritic.critic import load_critic
    cards = sorted(critics_dir.glob("*.json"))
    if not cards:
        print("No critic cards found in critics/.")
        return

    print(f"{'ID':<14} {'Theorist':<24} {'Book':<36} {'Items'}")
    print("-" * 90)
    for card_path in cards:
        try:
            critic = load_critic(card_path)
            print(f"{critic.critic_id:<14} {critic.theorist:<24} {critic.book:<36} {len(critic.items)} {critic.items_key}")
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
    """Run the critic-driven improvement loop."""
    # Resolve critic card path
    card_path = Path(f"critics/{args.critic}.json")
    if not card_path.exists():
        card_path = Path(args.critic)
        if not card_path.exists():
            print(f"Error: critic card not found: {args.critic}")
            try:
                available = ", ".join(p.stem for p in Path("critics").glob("*.json"))
                print(f"Available: {available}")
            except Exception:
                pass
            sys.exit(1)

    # Check wolframDrawer server
    from autocritic.adapters.wolfram import check_server
    if not check_server(args.wolfram_url):
        print(f"Error: wolframDrawer server not reachable at {args.wolfram_url}")
        print("Start it with: cd wolframDrawer && python3 run_local.py")
        sys.exit(1)

    print(f"wolframDrawer server OK at {args.wolfram_url}")

    # Build config
    from autocritic.loop import LoopConfig, run_loop
    from autocritic.adapters.wolfram import (
        WOLFRAM_PARAM_SPACE,
        DEFAULT_WOLFRAM_PARAMS,
        acquire_image,
    )

    config = LoopConfig(
        critic_card_path=card_path,
        model=args.model,
        max_iterations=args.iterations,
        damping=args.damping,
        intent=args.intent,
        output_dir=Path(args.output_dir),
        generator_name="wolfram",
        generator_base_url=args.wolfram_url,
    )

    # Initial params
    initial_params = dict(DEFAULT_WOLFRAM_PARAMS)
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
        return acquire_image(params, output_path, base_url=args.wolfram_url)

    result = run_loop(
        config=config,
        param_space=WOLFRAM_PARAM_SPACE,
        acquire_image_fn=acquire,
        initial_params=initial_params,
    )

    print(f"\nBest params:")
    for k, v in result.final_params.items():
        print(f"  {k}: {v}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="autocritic",
        description="Critic-card-driven image evaluation using art theory and LLMs.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # --- run ---
    run_parser = subparsers.add_parser("run", help="Run the improvement loop")
    run_parser.add_argument(
        "--critic", default="wolfflin",
        help="Critic card name or path (default: wolfflin).",
    )
    run_parser.add_argument(
        "--model", default="openai:gpt-4o",
        help="LLM model string, e.g. 'openai:gpt-5.4-mini' (default: openai:gpt-4o).",
    )
    run_parser.add_argument("--iterations", type=int, default=10, help="Max iterations (default: 10).")
    run_parser.add_argument("--intent", help="Project intent for the critic.")
    run_parser.add_argument("--wolfram-url", default="http://127.0.0.1:8010", help="wolframDrawer server URL.")
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
