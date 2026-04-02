"""
Eval runner: discovers and executes eval suites, collects results, persists JSON.

Eval suites:
  - programmatic: structural validation, vocabulary checks, ground-truth alignment
    (fast, no API key needed)
  - usefulness: critique specificity, actionability, lens grounding
    (requires API key — LLM-as-judge)
  - fidelity: citation grounding, lens specificity vs generic baseline
    (requires API key — LLM-as-judge)

Each suite is a collection of eval functions that return EvalResult objects.
Results are saved as JSON and printed as a summary table.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from autocritic.critic import load_critic, _ITEMS_KEYS, _ID_FIELDS
from evals.ground_truth import THEORISTS
from evals.fixtures.generic_baseline import GENERIC_VOCABULARY
from evals.judge import EvalResult, run_programmatic_check, run_vocabulary_check


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CRITICS_DIR = Path(__file__).resolve().parent.parent / "critics"
RESULTS_DIR = Path(__file__).resolve().parent / "results"

REQUIRED_TOP_LEVEL = [
    "critic_id", "theorist", "book", "thesis", "anti_goals", "tensions",
]
REQUIRED_ITEM_FIELDS = ["label", "definition", "diagnostic_questions"]


# ---------------------------------------------------------------------------
# Run result
# ---------------------------------------------------------------------------

@dataclass
class RunResult:
    """Collected results from a single eval run."""

    suite: str
    timestamp: str
    duration_seconds: float
    results: list[EvalResult]
    summary: dict[str, Any] = field(default_factory=dict)

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if not r.passed)

    @property
    def total(self) -> int:
        return len(self.results)

    def to_dict(self) -> dict[str, Any]:
        return {
            "suite": self.suite,
            "timestamp": self.timestamp,
            "duration_seconds": round(self.duration_seconds, 2),
            "passed": self.passed,
            "failed": self.failed,
            "total": self.total,
            "results": [
                {
                    "eval_name": r.eval_name,
                    "passed": r.passed,
                    "total_score": r.total_score,
                    "max_score": r.max_score,
                    "scores": [
                        {
                            "dimension": s.dimension,
                            "score": s.score,
                            "evidence": s.evidence,
                        }
                        for s in r.scores
                    ],
                    "failure_evidence": r.failure_evidence,
                    "judge_reasoning": r.judge_reasoning,
                }
                for r in self.results
            ],
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_card_text(card: dict) -> str:
    """Flatten a critic card into searchable text for vocabulary checks."""
    parts = [card.get("thesis", "")]
    for key in _ITEMS_KEYS:
        for item in card.get(key, []):
            parts.append(item.get("definition", ""))
            parts.extend(item.get("diagnostic_questions", []))
            fd = item.get("feedback_directions", {})
            if isinstance(fd, dict):
                for v in fd.values():
                    if isinstance(v, list):
                        parts.extend(v)
            elif isinstance(fd, list):
                parts.extend(fd)
            parts.extend(item.get("examples", []))
            ind = item.get("indicators", {})
            if isinstance(ind, dict):
                for v in ind.values():
                    if isinstance(v, list):
                        parts.extend(v)
            parts.extend(item.get("common_misreadings", []))
    for ag in card.get("anti_goals", []):
        parts.append(ag)
    return " ".join(parts).lower()


def _find_cards(critic_filter: str | None = None) -> list[Path]:
    """Return critic card paths, optionally filtered to a single card."""
    if critic_filter:
        path = CRITICS_DIR / f"{critic_filter}.json"
        if not path.exists():
            raise FileNotFoundError(f"Critic card not found: {path}")
        return [path]
    return sorted(CRITICS_DIR.glob("*.json"))


# ---------------------------------------------------------------------------
# Programmatic eval suite
# ---------------------------------------------------------------------------

def _eval_structure(card_path: Path, card: dict) -> EvalResult:
    """Check structural requirements for a critic card."""
    name = card_path.stem
    checks: list[tuple[str, bool, str]] = []

    # Top-level fields
    missing = [f for f in REQUIRED_TOP_LEVEL if f not in card]
    checks.append((
        "top_level_fields",
        len(missing) == 0,
        f"missing: {missing}" if missing else f"all {len(REQUIRED_TOP_LEVEL)} present",
    ))

    # critic_id matches filename
    checks.append((
        "id_matches_filename",
        card.get("critic_id") == name,
        f"critic_id='{card.get('critic_id')}', filename='{name}'",
    ))

    # Has items
    critic = load_critic(card_path)
    checks.append((
        "has_items",
        len(critic.items) >= 2,
        f"{len(critic.items)} items found",
    ))

    # Items have core fields
    bad_items = []
    for item in critic.items:
        label = item.get("label", "?")
        missing_fields = [f for f in REQUIRED_ITEM_FIELDS if f not in item]
        if missing_fields:
            bad_items.append(f"{label} missing {missing_fields}")
    checks.append((
        "item_fields",
        len(bad_items) == 0,
        "; ".join(bad_items) if bad_items else "all items have required fields",
    ))

    # Has anti-goals
    checks.append((
        "has_anti_goals",
        len(card.get("anti_goals", [])) >= 2,
        f"{len(card.get('anti_goals', []))} anti-goals",
    ))

    # Has citations
    checks.append((
        "has_citations",
        len(card.get("citations", [])) >= 3,
        f"{len(card.get('citations', []))} citations",
    ))

    # Items have recognized ID fields
    id_fields_set = set(_ID_FIELDS)
    items_without_id = []
    for item in critic.all_items:
        if not any(idf in item for idf in id_fields_set):
            items_without_id.append(item.get("label", "?"))
    checks.append((
        "item_id_fields",
        len(items_without_id) == 0,
        f"missing ID: {items_without_id}" if items_without_id else "all items have ID fields",
    ))

    return run_programmatic_check(f"structure/{name}", checks)


def _eval_vocabulary(card_path: Path, card: dict) -> list[EvalResult]:
    """Check vocabulary distinctiveness against ground truth."""
    name = card_path.stem
    gt = THEORISTS.get(name)
    if gt is None:
        return []

    text = _extract_card_text(card)
    results = []

    # Distinctive vocabulary presence
    vocab = [v.lower() for v in gt.DISTINCTIVE_VOCABULARY]
    hits = [v for v in vocab if v in text]
    ratio = len(hits) / len(vocab) if vocab else 0
    missing = sorted(set(vocab) - set(hits))
    results.append(run_programmatic_check(f"vocabulary/{name}", [
        (
            "distinctive_coverage",
            ratio >= 0.4,
            f"{len(hits)}/{len(vocab)} ({ratio:.0%}) distinctive terms"
            + (f"; missing: {missing}" if ratio < 0.4 else ""),
        ),
    ]))

    # Generic dominance check
    distinctive_hits = sum(1 for v in gt.DISTINCTIVE_VOCABULARY if v.lower() in text)
    generic_hits = sum(1 for v in GENERIC_VOCABULARY if v.lower() in text)
    results.append(run_programmatic_check(f"generic_dominance/{name}", [
        (
            "distinctive_vs_generic",
            distinctive_hits >= generic_hits * 0.8,
            f"distinctive={distinctive_hits} vs generic={generic_hits}",
        ),
    ]))

    return results


def _eval_ground_truth_quality(name: str) -> list[EvalResult]:
    """Validate that the ground truth module itself is well-formed."""
    gt = THEORISTS.get(name)
    if gt is None:
        return []

    checks: list[tuple[str, bool, str]] = []

    checks.append((
        "essential_claims",
        len(gt.ESSENTIAL_CLAIMS) >= 3,
        f"{len(gt.ESSENTIAL_CLAIMS)} claims",
    ))
    checks.append((
        "anti_goals",
        len(gt.ANTI_GOALS) >= 3,
        f"{len(gt.ANTI_GOALS)} anti-goals",
    ))
    checks.append((
        "distinctive_vocabulary",
        len(gt.DISTINCTIVE_VOCABULARY) >= 8,
        f"{len(gt.DISTINCTIVE_VOCABULARY)} terms",
    ))

    # Good example should use more distinctive vocab than bad example
    good = gt.GOOD_CRITIQUE_EXAMPLE.lower()
    bad = gt.BAD_CRITIQUE_EXAMPLE.lower()
    vocab = [v.lower() for v in gt.DISTINCTIVE_VOCABULARY]
    good_hits = sum(1 for v in vocab if v in good)
    bad_hits = sum(1 for v in vocab if v in bad)
    checks.append((
        "example_differentiation",
        good_hits > bad_hits,
        f"good={good_hits} vs bad={bad_hits} distinctive terms",
    ))

    return [run_programmatic_check(f"ground_truth/{name}", checks)]


def _eval_vocabulary_overlap() -> list[EvalResult]:
    """Check that theorists' vocabularies don't overlap excessively."""
    names = list(THEORISTS.keys())
    checks: list[tuple[str, bool, str]] = []

    for i, name_a in enumerate(names):
        vocab_a = set(v.lower() for v in THEORISTS[name_a].DISTINCTIVE_VOCABULARY)
        for name_b in names[i + 1:]:
            vocab_b = set(v.lower() for v in THEORISTS[name_b].DISTINCTIVE_VOCABULARY)
            overlap = vocab_a & vocab_b
            smaller = min(len(vocab_a), len(vocab_b))
            ratio = len(overlap) / smaller if smaller > 0 else 0
            checks.append((
                f"{name_a}_vs_{name_b}",
                ratio <= 0.3,
                f"{len(overlap)}/{smaller} ({ratio:.0%})"
                + (f" shared: {sorted(overlap)}" if ratio > 0.3 else ""),
            ))

    return [run_programmatic_check("vocabulary_overlap", checks)]


def run_programmatic_suite(critic_filter: str | None = None) -> RunResult:
    """Run all programmatic evals (no API key needed)."""
    start = time.monotonic()
    results: list[EvalResult] = []

    cards = _find_cards(critic_filter)
    for card_path in cards:
        card = json.loads(card_path.read_text())
        name = card_path.stem

        # Structure
        results.append(_eval_structure(card_path, card))

        # Vocabulary (only for cards with ground truth)
        results.extend(_eval_vocabulary(card_path, card))

        # Ground truth quality
        results.extend(_eval_ground_truth_quality(name))

    # Cross-card checks (only when running all)
    if critic_filter is None:
        results.extend(_eval_vocabulary_overlap())

    duration = time.monotonic() - start
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    return RunResult(
        suite="programmatic",
        timestamp=timestamp,
        duration_seconds=duration,
        results=results,
    )


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def save_results(run_result: RunResult) -> Path:
    """Save run results as JSON and return the file path."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{run_result.timestamp}_{run_result.suite}.json"
    path = RESULTS_DIR / filename
    path.write_text(json.dumps(run_result.to_dict(), indent=2) + "\n")
    return path


def print_summary(run_result: RunResult) -> None:
    """Print a summary table to stdout."""
    print(f"\n{'=' * 72}")
    print(f"  Eval suite: {run_result.suite}")
    print(f"  Timestamp:  {run_result.timestamp}")
    print(f"  Duration:   {run_result.duration_seconds:.2f}s")
    print(f"{'=' * 72}\n")

    # Group results by category (part before /)
    categories: dict[str, list[EvalResult]] = {}
    for r in run_result.results:
        cat = r.eval_name.split("/")[0] if "/" in r.eval_name else r.eval_name
        categories.setdefault(cat, []).append(r)

    for cat, evals in categories.items():
        cat_pass = sum(1 for e in evals if e.passed)
        cat_total = len(evals)
        status = "PASS" if cat_pass == cat_total else "FAIL"
        print(f"  {cat:<28} {cat_pass}/{cat_total}  {status}")

        for e in evals:
            mark = "  pass" if e.passed else "**FAIL"
            score_str = f"{e.total_score}/{e.max_score}"
            print(f"    {mark}  {e.eval_name:<36} {score_str:>7}")

            # Show failure details
            if not e.passed:
                for s in e.scores:
                    if s.score == 0:
                        print(f"           {s.dimension}: {s.evidence}")

    print(f"\n{'─' * 72}")
    print(f"  Total: {run_result.passed}/{run_result.total} passed", end="")
    if run_result.failed > 0:
        print(f"  ({run_result.failed} failed)", end="")
    print(f"  [{run_result.duration_seconds:.2f}s]")
    print()
