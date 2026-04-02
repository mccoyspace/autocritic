"""
Usefulness eval suite: tests whether critic cards produce specific, actionable,
lens-grounded critiques rather than generic art coaching.

Two layers:
  - Programmatic checks on cached critique fixtures (no extra LLM calls)
  - LLM-as-judge checks for actionability and anti-generic distinctiveness

Fixtures are pre-generated ScoredCritique objects saved as JSON.
Regenerate with: autocritic eval --suite usefulness --refresh
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from autocritic.critic import CritiqueResult, load_critic
from autocritic.scoring import AxisScore, ScoredCritique

from evals.fixtures.generic_baseline import GENERIC_CRITIQUE, GENERIC_VOCABULARY
from evals.ground_truth import THEORISTS
from evals.judge import EvalResult, run_comparative_judge, run_judge, run_programmatic_check
from evals.rubrics.usefulness import (
    EXPECTATIONS,
    FIXTURES_DIR,
    MIN_DIRECTIVE_WORDS,
    REQUIRED_SECTIONS,
    CritiqueExpectation,
)
from evals.runner import CRITICS_DIR, RunResult


# ---------------------------------------------------------------------------
# Fixture serialization
# ---------------------------------------------------------------------------

def _serialize_scored_critique(sc: ScoredCritique) -> dict[str, Any]:
    """Convert a ScoredCritique to a JSON-serializable dict."""
    return {
        "critique": {
            "critic_id": sc.critique.critic_id,
            "image_path": sc.critique.image_path,
            "model": sc.critique.model,
            "raw_text": sc.critique.raw_text,
            "lens_summary": sc.critique.lens_summary,
            "strengths": sc.critique.strengths,
            "weaknesses": sc.critique.weaknesses,
            "criterion_notes": sc.critique.criterion_notes,
            "directives": sc.critique.directives,
        },
        "axis_scores": [
            {
                "axis_id": s.axis_id,
                "label": s.label,
                "score": s.score,
                "reasoning": s.reasoning,
            }
            for s in sc.axis_scores
        ],
        "composite_score": sc.composite_score,
    }


def _deserialize_scored_critique(data: dict[str, Any]) -> ScoredCritique:
    """Reconstruct a ScoredCritique from saved JSON."""
    c = data["critique"]
    critique = CritiqueResult(
        critic_id=c["critic_id"],
        image_path=c["image_path"],
        model=c["model"],
        raw_text=c["raw_text"],
        lens_summary=c.get("lens_summary", ""),
        strengths=c.get("strengths", []),
        weaknesses=c.get("weaknesses", []),
        criterion_notes=c.get("criterion_notes", []),
        directives=c.get("directives", []),
    )
    axis_scores = [
        AxisScore(
            axis_id=s["axis_id"],
            label=s["label"],
            score=s["score"],
            reasoning=s["reasoning"],
        )
        for s in data.get("axis_scores", [])
    ]
    return ScoredCritique(
        critique=critique,
        axis_scores=axis_scores,
        composite_score=data.get("composite_score", 0.0),
    )


def load_fixture(expectation: CritiqueExpectation) -> ScoredCritique | None:
    """Load a cached critique fixture, or return None if missing."""
    path = expectation.fixture_path
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    return _deserialize_scored_critique(data)


def generate_fixture(
    expectation: CritiqueExpectation,
    model: str = "claude-sonnet-4-20250514",
) -> ScoredCritique:
    """Generate a critique fixture by running the critic against the image."""
    from autocritic.scoring import score_critique

    card_path = CRITICS_DIR / f"{expectation.critic_id}.json"
    critic = load_critic(card_path)

    scored = score_critique(
        critic,
        expectation.image_path,
        model=model,
    )

    # Save fixture
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    expectation.fixture_path.write_text(
        json.dumps(_serialize_scored_critique(scored), indent=2) + "\n"
    )

    return scored


def generate_all_fixtures(
    model: str = "claude-sonnet-4-20250514",
    force: bool = False,
) -> dict[str, ScoredCritique]:
    """Generate all missing fixtures (or all if force=True)."""
    results = {}
    for exp in EXPECTATIONS:
        if not exp.image_path.exists():
            print(f"  skip {exp.critic_id}/{exp.image_name}: image not found")
            continue
        if not force and exp.fixture_path.exists():
            print(f"  cached {exp.critic_id}/{exp.image_name}")
            results[f"{exp.critic_id}/{exp.image_name}"] = load_fixture(exp)
            continue
        print(f"  generating {exp.critic_id}/{exp.image_name}...")
        results[f"{exp.critic_id}/{exp.image_name}"] = generate_fixture(exp, model)
    return results


# ---------------------------------------------------------------------------
# Programmatic usefulness checks
# ---------------------------------------------------------------------------

def eval_completeness(
    exp: CritiqueExpectation,
    sc: ScoredCritique,
) -> EvalResult:
    """Check that the critique has all required non-empty sections."""
    checks: list[tuple[str, bool, str]] = []

    # Lens summary
    has_summary = bool(sc.critique.lens_summary.strip())
    checks.append((
        "lens_summary",
        has_summary,
        f"{len(sc.critique.lens_summary)} chars" if has_summary else "empty",
    ))

    # Strengths
    has_strengths = len(sc.critique.strengths) >= 1
    checks.append((
        "strengths",
        has_strengths,
        f"{len(sc.critique.strengths)} items" if has_strengths else "none",
    ))

    # Weaknesses
    has_weaknesses = len(sc.critique.weaknesses) >= 1
    checks.append((
        "weaknesses",
        has_weaknesses,
        f"{len(sc.critique.weaknesses)} items" if has_weaknesses else "none",
    ))

    # Directives
    has_directives = len(sc.critique.directives) >= 1
    checks.append((
        "directives",
        has_directives,
        f"{len(sc.critique.directives)} items" if has_directives else "none",
    ))

    # Directive substantiveness — not just one-word items
    if sc.critique.directives:
        short = [d for d in sc.critique.directives if len(d.split()) < MIN_DIRECTIVE_WORDS]
        checks.append((
            "directive_substance",
            len(short) == 0,
            f"{len(short)} too-short directives" if short else "all substantive",
        ))

    # Axis scores present
    checks.append((
        "axis_scores",
        len(sc.axis_scores) >= 2,
        f"{len(sc.axis_scores)} axes scored",
    ))

    # Axis score reasoning non-empty
    empty_reasoning = [s for s in sc.axis_scores if not s.reasoning.strip()]
    checks.append((
        "score_reasoning",
        len(empty_reasoning) == 0,
        f"{len(empty_reasoning)} missing" if empty_reasoning else "all have reasoning",
    ))

    return run_programmatic_check(
        f"completeness/{exp.critic_id}_{exp.image_name}",
        checks,
    )


def eval_lens_vocabulary(
    exp: CritiqueExpectation,
    sc: ScoredCritique,
) -> EvalResult:
    """Check that the critique output uses the theorist's vocabulary."""
    gt = THEORISTS.get(exp.critic_id)
    if gt is None:
        return run_programmatic_check(
            f"lens_vocabulary/{exp.critic_id}_{exp.image_name}",
            [("ground_truth_exists", False, "no ground truth module")],
        )

    # Search the full critique text (raw response + parsed fields)
    text = sc.critique.raw_text.lower()

    distinctive = gt.DISTINCTIVE_VOCABULARY
    distinctive_hits = sum(1 for v in distinctive if v.lower() in text)
    generic_hits = sum(1 for v in GENERIC_VOCABULARY if v.lower() in text)

    distinctive_ratio = distinctive_hits / len(distinctive) if distinctive else 0

    checks: list[tuple[str, bool, str]] = [
        (
            "distinctive_presence",
            distinctive_ratio >= 0.3,
            f"{distinctive_hits}/{len(distinctive)} ({distinctive_ratio:.0%}) distinctive terms",
        ),
        (
            "distinctive_over_generic",
            distinctive_hits >= generic_hits * 0.8,
            f"distinctive={distinctive_hits} vs generic={generic_hits}"
            f" (threshold: {generic_hits * 0.8:.0f})",
        ),
    ]

    return run_programmatic_check(
        f"lens_vocabulary/{exp.critic_id}_{exp.image_name}",
        checks,
    )


def eval_expected_terms(
    exp: CritiqueExpectation,
    sc: ScoredCritique,
) -> EvalResult:
    """Check that expected terms for this image-critic pair appear."""
    text = sc.critique.raw_text.lower()

    hits = [t for t in exp.expected_terms if t.lower() in text]
    misses = [t for t in exp.expected_terms if t.lower() not in text]
    ratio = len(hits) / len(exp.expected_terms) if exp.expected_terms else 0

    # Require at least 75% of expected terms
    checks: list[tuple[str, bool, str]] = [
        (
            "expected_term_coverage",
            ratio >= 0.75,
            f"{len(hits)}/{len(exp.expected_terms)} ({ratio:.0%})"
            + (f"; missing: {misses}" if misses else ""),
        ),
    ]

    return run_programmatic_check(
        f"expected_terms/{exp.critic_id}_{exp.image_name}",
        checks,
    )


def eval_score_text_coherence(
    exp: CritiqueExpectation,
    sc: ScoredCritique,
) -> EvalResult:
    """Check basic coherence between axis scores and written text.

    For now, a simple check: axes scored low (below threshold) should have
    their label or axis_id mentioned somewhere in weaknesses or directives.
    If a score is poor but the text never mentions it, the critique isn't
    internally coherent.
    """
    checks: list[tuple[str, bool, str]] = []

    # Combine weaknesses + directives text for searching
    concern_text = " ".join(sc.critique.weaknesses + sc.critique.directives).lower()

    # Determine which axes are "low" — different thresholds for bipolar vs unipolar
    card_path = CRITICS_DIR / f"{exp.critic_id}.json"
    critic = load_critic(card_path)
    from autocritic.scoring import is_bipolar
    bipolar = is_bipolar(critic)

    low_axes = []
    for s in sc.axis_scores:
        if bipolar:
            # For bipolar, low commitment (near 0) is notable
            if abs(s.score) < 0.2:
                low_axes.append(s)
        else:
            # For unipolar, below 0.4 is notably weak
            if s.score < 0.4:
                low_axes.append(s)

    if not low_axes:
        # No low-scoring axes — coherence is trivially satisfied
        checks.append((
            "low_score_coverage",
            True,
            "no low-scoring axes to check",
        ))
    else:
        mentioned = 0
        for s in low_axes:
            # Check if axis label or id appears in concern text
            label_found = s.label.lower() in concern_text
            id_found = s.axis_id.lower() in concern_text
            # Also check individual words from the label (e.g. "linear" from "Linear vs. Painterly")
            label_words = [w.lower() for w in s.label.replace("vs.", "").split() if len(w) > 3]
            word_found = any(w in concern_text for w in label_words)
            if label_found or id_found or word_found:
                mentioned += 1

        ratio = mentioned / len(low_axes)
        checks.append((
            "low_score_coverage",
            ratio >= 0.5,
            f"{mentioned}/{len(low_axes)} low-scoring axes addressed in weaknesses/directives",
        ))

    return run_programmatic_check(
        f"coherence/{exp.critic_id}_{exp.image_name}",
        checks,
    )


# ---------------------------------------------------------------------------
# LLM-as-judge usefulness checks
# ---------------------------------------------------------------------------

def eval_actionability(
    exp: CritiqueExpectation,
    sc: ScoredCritique,
    model: str = "claude-sonnet-4-20250514",
) -> EvalResult:
    """Judge whether the critique's directives are actionable by a translator."""
    directives_text = "\n".join(f"- {d}" for d in sc.critique.directives)
    weaknesses_text = "\n".join(f"- {w}" for w in sc.critique.weaknesses)

    artifact = (
        f"## Critic: {exp.critic_id}\n"
        f"## Image: {exp.image_name}\n\n"
        f"## Directives\n{directives_text}\n\n"
        f"## Weaknesses\n{weaknesses_text}\n\n"
        f"## Lens Summary\n{sc.critique.lens_summary}"
    )

    return run_judge(
        eval_name=f"actionability/{exp.critic_id}_{exp.image_name}",
        artifact_description=(
            f"Directives and weaknesses from a {exp.critic_id} critique of "
            f"{exp.image_name}, evaluated for actionability"
        ),
        artifact_content=artifact,
        rubric_dimensions=[
            "specificity: directives reference visible features, not abstractions",
            "directionality: each directive implies a clear change direction",
            "non-contradiction: directives do not work against each other",
            "parameter-mappability: a parameter-tuner could act on these",
        ],
        failure_modes=[
            "vague advice like 'improve the composition' or 'add more variety'",
            "directives that reference art-historical knowledge rather than visible features",
            "contradictory directives that cancel each other out",
            "directives so abstract that no parameter change could address them",
        ],
        pass_threshold=10,
        model=model,
    )


def eval_anti_generic(
    exp: CritiqueExpectation,
    sc: ScoredCritique,
    model: str = "claude-sonnet-4-20250514",
) -> EvalResult:
    """Judge whether the critique is distinct from generic design feedback."""
    # Build a condensed version of the critique for comparison
    critique_text = (
        f"Lens: {sc.critique.lens_summary}\n\n"
        f"Strengths:\n"
        + "\n".join(f"- {s}" for s in sc.critique.strengths)
        + "\n\nWeaknesses:\n"
        + "\n".join(f"- {w}" for w in sc.critique.weaknesses)
        + "\n\nDirectives:\n"
        + "\n".join(f"- {d}" for d in sc.critique.directives)
    )

    return run_comparative_judge(
        eval_name=f"anti_generic/{exp.critic_id}_{exp.image_name}",
        description=(
            f"Compare a {exp.critic_id} critique against a generic design "
            f"critique to verify lens specificity in the output"
        ),
        artifact_a=critique_text,
        artifact_b=GENERIC_CRITIQUE,
        comparison_dimensions=[
            "distinctive vocabulary: uses theorist-specific terms",
            "evaluative framework: applies a specific theory, not generic principles",
            "observation specificity: names features this theorist cares about",
            "anti-goal awareness: avoids generic design-coach language",
        ],
        pass_threshold=10,
        model=model,
    )


# ---------------------------------------------------------------------------
# Suite runner
# ---------------------------------------------------------------------------

def run_usefulness_suite(
    critic_filter: str | None = None,
    model: str = "claude-sonnet-4-20250514",
    refresh: bool = False,
    include_judge: bool = False,
) -> RunResult:
    """Run the usefulness eval suite.

    Args:
        critic_filter: Run only for this critic (or all if None).
        model: LLM model for fixture generation and judge evals.
        refresh: If True, regenerate all fixtures before evaluating.
        include_judge: If True, run LLM-as-judge evals (requires API key).
    """
    start = time.monotonic()
    results: list[EvalResult] = []
    skipped = 0

    # Filter expectations
    expectations = EXPECTATIONS
    if critic_filter:
        expectations = [e for e in EXPECTATIONS if e.critic_id == critic_filter]
        if not expectations:
            raise ValueError(
                f"No usefulness expectations defined for critic '{critic_filter}'. "
                f"Available: {sorted(set(e.critic_id for e in EXPECTATIONS))}"
            )

    for exp in expectations:
        # Check image exists
        if not exp.image_path.exists():
            print(f"  skip {exp.critic_id}/{exp.image_name}: image not found")
            skipped += 1
            continue

        # Load or generate fixture
        if refresh or not exp.fixture_path.exists():
            print(f"  generating {exp.critic_id}/{exp.image_name}...", flush=True)
            try:
                sc = generate_fixture(exp, model)
            except Exception as e:
                print(f"  ERROR generating {exp.critic_id}/{exp.image_name}: {e}")
                results.append(run_programmatic_check(
                    f"fixture_generation/{exp.critic_id}_{exp.image_name}",
                    [("generation", False, str(e))],
                ))
                continue
        else:
            sc = load_fixture(exp)
            if sc is None:
                print(f"  skip {exp.critic_id}/{exp.image_name}: fixture load failed")
                skipped += 1
                continue

        # Programmatic checks
        results.append(eval_completeness(exp, sc))
        results.append(eval_lens_vocabulary(exp, sc))
        results.append(eval_expected_terms(exp, sc))
        results.append(eval_score_text_coherence(exp, sc))

        # LLM-as-judge checks (optional)
        if include_judge:
            tag = f"{exp.critic_id}/{exp.image_name}"
            print(f"  judging actionability: {tag}...", flush=True)
            results.append(eval_actionability(exp, sc, model))
            print(f"  judging anti-generic: {tag}...", flush=True)
            results.append(eval_anti_generic(exp, sc, model))

    duration = time.monotonic() - start
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    return RunResult(
        suite="usefulness",
        timestamp=timestamp,
        duration_seconds=duration,
        results=results,
        summary={"skipped": skipped, "include_judge": include_judge},
    )
