"""
Improvement loop: generate → critique → translate → adjust → repeat.

Orchestrates the feedback cycle between a generative system (via an adapter)
and the critic runtime. Tracks trajectory, handles accept/reject logic,
and saves artifacts per iteration.
"""

from __future__ import annotations

import json
import shutil
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from collections.abc import Callable
from typing import Any

from autocritic.critic import CriticCard, load_critic
from autocritic.scoring import ScoredCritique, compare_scores, is_bipolar, score_critique
from autocritic.translator import (
    ParamSpace,
    TranslationResult,
    TranslationParseError,
    apply_deltas,
    translate_critique_to_params,
)


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class IterationRecord:
    """Record of a single loop iteration."""
    iteration: int
    params: dict[str, Any]
    image_path: str
    composite_score: float
    accepted: bool
    axis_scores_summary: list[dict[str, Any]] = field(default_factory=list)
    deltas: dict[str, Any] = field(default_factory=dict)
    delta_reasoning: str = ""
    lens_summary: str = ""
    directives: list[str] = field(default_factory=list)


@dataclass
class LoopConfig:
    """Configuration for an improvement loop run.

    Note: ``min_improvement`` and ``max_consecutive_rejections`` only
    apply to unipolar critics.  Bipolar critics accept all iterations
    (pole movement is not monotonic improvement) and converge via
    plateau detection or ``max_iterations``.
    """
    critic_card_path: Path
    model: str = "claude-sonnet-4-20250514"
    max_iterations: int = 10
    min_improvement: float = 0.02
    damping: float = 0.7
    max_consecutive_rejections: int = 2
    intent: str | None = None
    output_dir: Path = Path("runs")

    # Generator-specific (set by adapter)
    generator_name: str = "rewriter"
    generator_base_url: str = "http://127.0.0.1:8010"


@dataclass
class LoopResult:
    """Result of a completed improvement loop."""
    run_id: str
    iterations: list[IterationRecord]
    final_params: dict[str, Any]
    best_iteration: int
    best_score: float
    output_dir: Path
    stop_reason: str
    parse_errors: int = 0


# ---------------------------------------------------------------------------
# Artifact saving
# ---------------------------------------------------------------------------

def _save_iteration(run_dir: Path, record: IterationRecord) -> None:
    """Save artifacts for a single iteration."""
    iter_dir = run_dir / f"iter_{record.iteration:03d}"
    iter_dir.mkdir(parents=True, exist_ok=True)

    # Params
    (iter_dir / "params.json").write_text(
        json.dumps(record.params, indent=2)
    )

    # Score summary
    summary = {
        "iteration": record.iteration,
        "composite_score": record.composite_score,
        "accepted": record.accepted,
        "axis_scores": record.axis_scores_summary,
        "lens_summary": record.lens_summary,
        "directives": record.directives,
    }
    (iter_dir / "critique_summary.json").write_text(
        json.dumps(summary, indent=2)
    )

    # Deltas (if any)
    if record.deltas:
        delta_data = {
            "deltas": record.deltas,
            "reasoning": record.delta_reasoning,
        }
        (iter_dir / "deltas.json").write_text(
            json.dumps(delta_data, indent=2)
        )

    # Copy image (skip if already in the iter directory)
    src = Path(record.image_path)
    dst = iter_dir / f"image{src.suffix}"
    if src.exists() and src.resolve() != dst.resolve():
        shutil.copy2(src, dst)


def _save_trajectory(run_dir: Path, iterations: list[IterationRecord]) -> None:
    """Save the score trajectory across all iterations."""
    trajectory = {
        "iterations": [
            {
                "iteration": r.iteration,
                "composite_score": r.composite_score,
                "accepted": r.accepted,
                "n_deltas": len(r.deltas),
            }
            for r in iterations
        ],
    }
    (run_dir / "trajectory.json").write_text(
        json.dumps(trajectory, indent=2)
    )


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def run_loop(
    config: LoopConfig,
    param_space: ParamSpace,
    acquire_image_fn: Callable[[dict[str, Any], Path], Path],
    initial_params: dict[str, Any] | None = None,
) -> LoopResult:
    """Run the improvement loop.

    Args:
        config: Loop configuration
        param_space: Parameter space definition for the generator
        acquire_image_fn: Callable that generates an image from params.
            Signature: (params: dict, output_path: Path) -> Path
        initial_params: Starting parameters (defaults if None)

    Returns:
        LoopResult with all iteration records and the best parameters.
    """
    # Setup
    run_id = f"{config.generator_name}_{int(time.time())}"
    run_dir = Path(config.output_dir) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    critic = load_critic(config.critic_card_path)
    bipolar = is_bipolar(critic)
    params = initial_params or param_space.defaults()

    # Save config
    config_data = {
        "run_id": run_id,
        "critic_id": critic.critic_id,
        "model": config.model,
        "max_iterations": config.max_iterations,
        "min_improvement": config.min_improvement,
        "damping": config.damping,
        "intent": config.intent,
        "initial_params": params,
    }
    (run_dir / "config.json").write_text(json.dumps(config_data, indent=2))

    # State
    iterations: list[IterationRecord] = []
    best_score = -1.0
    best_iteration = 0
    best_params = dict(params)
    accepted_score = -1.0
    accepted_params = dict(params)
    consecutive_rejections = 0
    parse_errors = 0
    last_deltas: dict[str, Any] = {}
    stop_reason = "max_iterations"

    for i in range(config.max_iterations):
        print(f"\n{'='*60}")
        print(f"Iteration {i}")
        print(f"{'='*60}")

        # 1. Generate image
        image_path = run_dir / f"iter_{i:03d}" / "image.png"
        print(f"  Generating image with params...")
        image_path = acquire_image_fn(params, image_path)
        print(f"  Image: {image_path}")

        # 2. Score critique (one LLM vision call)
        print(f"  Critiquing via {critic.critic_id} ({config.model})...")
        scored = score_critique(
            critic, image_path,
            model=config.model,
            intent=config.intent,
        )
        print(f"  Composite score: {scored.composite_score:.3f}")
        for s in scored.axis_scores:
            print(f"    {s.label}: {s.score:.2f} — {s.reasoning[:60]}")

        # 3. Accept/reject
        # For bipolar critics, composite = mean(abs(score)) measures pole-
        # commitment, not quality.  A shift from one pole toward the other
        # can look like regression but is valid aesthetic movement.  Accept
        # all iterations for bipolar critics; the loop still converges via
        # plateau detection and max-iterations.
        if i == 0:
            accepted = True
            print(f"  Baseline (accepted)")
        elif bipolar:
            # Always accept — bipolar movement is not monotonic
            accepted = True
            consecutive_rejections = 0
            delta = scored.composite_score - accepted_score
            print(f"  Bipolar critic: accepted (Δ{delta:+.3f})")
        elif scored.composite_score - accepted_score >= config.min_improvement:
            accepted = True
            consecutive_rejections = 0
            print(f"  Improved by {scored.composite_score - accepted_score:.3f} (accepted)")
        else:
            accepted = False
            consecutive_rejections += 1
            delta = scored.composite_score - accepted_score
            print(f"  No improvement ({delta:+.3f}), rejection {consecutive_rejections}/{config.max_consecutive_rejections}")

        # Track best score unconditionally
        if scored.composite_score > best_score:
            best_score = scored.composite_score
            best_iteration = i
            best_params = dict(params)

        if accepted:
            accepted_score = scored.composite_score
            accepted_params = dict(params)

        # Build iteration record
        record = IterationRecord(
            iteration=i,
            params=dict(params),
            image_path=str(image_path),
            composite_score=scored.composite_score,
            accepted=accepted,
            axis_scores_summary=[
                {"axis_id": s.axis_id, "label": s.label,
                 "score": s.score, "reasoning": s.reasoning}
                for s in scored.axis_scores
            ],
            lens_summary=scored.critique.lens_summary,
            directives=scored.critique.directives,
        )

        # 4. Check stopping conditions
        if scored.composite_score > 0.9:
            record.deltas = {}
            iterations.append(record)
            _save_iteration(run_dir, record)
            stop_reason = "high_score"
            print(f"  Score > 0.9 — stopping")
            break

        if i >= 3:
            # Include current score (not yet appended to iterations)
            recent = [r.composite_score for r in iterations[-2:]] + [scored.composite_score]
            if len(recent) >= 3 and max(recent) - min(recent) < 0.01:
                record.deltas = {}
                iterations.append(record)
                _save_iteration(run_dir, record)
                stop_reason = "plateaued"
                print(f"  Plateaued — stopping")
                break

        # 5. Handle rejections (unipolar only — bipolar critics accept all)
        if not bipolar:
            if not accepted and consecutive_rejections >= config.max_consecutive_rejections:
                # Revert to best and get fresh deltas
                print(f"  Max rejections reached — reverting to best (iter {best_iteration})")
                params = dict(best_params)
                consecutive_rejections = 0
                last_deltas = {}
                # Fall through to translation with reverted params
            elif not accepted and last_deltas:
                # Halve the previous deltas and revert
                print(f"  Reverting and halving deltas")
                params = dict(accepted_params)
                # Don't translate again — just retry with dampened deltas
                dampened = apply_deltas(
                    params, last_deltas, param_space,
                    damping=config.damping * 0.5,
                )
                record.deltas = last_deltas
                record.delta_reasoning = "Halved previous deltas after rejection"
                iterations.append(record)
                _save_iteration(run_dir, record)
                params = dampened
                continue

        # 6. Translate critique to parameter changes (one LLM text call)
        if i < config.max_iterations - 1:  # skip translation on last iteration
            print(f"  Translating critique to parameter changes...")
            try:
                translation = translate_critique_to_params(
                    scored,
                    params,
                    param_space,
                    model=config.model,
                    preservations=scored.critique.strengths,
                )
            except TranslationParseError as e:
                print(f"  Warning: translation parse failed: {e}")
                print(f"  Skipping parameter update this iteration.")
                parse_errors += 1
                consecutive_rejections += 1
                record.deltas = {}
                record.delta_reasoning = f"Parse error: {e}"
                iterations.append(record)
                _save_iteration(run_dir, record)
                continue

            print(f"  Deltas: {translation.deltas}")
            print(f"  Reasoning: {translation.reasoning[:100]}")

            record.deltas = translation.deltas
            record.delta_reasoning = translation.reasoning
            last_deltas = translation.deltas

            # Apply with damping
            params = apply_deltas(
                params, translation.deltas, param_space,
                damping=config.damping,
            )
        else:
            record.deltas = {}

        iterations.append(record)
        _save_iteration(run_dir, record)

    # Save trajectory
    _save_trajectory(run_dir, iterations)

    # Save final summary
    summary = {
        "run_id": run_id,
        "stop_reason": stop_reason,
        "total_iterations": len(iterations),
        "best_iteration": best_iteration,
        "best_score": best_score,
        "parse_errors": parse_errors,
        "final_params": best_params,
        "score_progression": [r.composite_score for r in iterations],
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2))

    # Generate contact sheet and narrative
    try:
        from autocritic.report import generate_contact_sheet, save_narrative_md
        sheet = generate_contact_sheet(run_dir)
        save_narrative_md(run_dir)
        print(f"\nContact sheet: {sheet}")
    except Exception as e:
        print(f"\nWarning: could not generate contact sheet: {e}")

    print(f"\n{'='*60}")
    print(f"Loop complete: {stop_reason}")
    print(f"Best score: {best_score:.3f} at iteration {best_iteration}")
    if parse_errors:
        print(f"Translation parse errors: {parse_errors}")
    print(f"Artifacts: {run_dir}")
    print(f"{'='*60}")

    return LoopResult(
        run_id=run_id,
        iterations=iterations,
        final_params=best_params,
        best_iteration=best_iteration,
        best_score=best_score,
        output_dir=run_dir,
        stop_reason=stop_reason,
        parse_errors=parse_errors,
    )
