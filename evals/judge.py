"""
Evaluation engine for autocritic — both programmatic and LLM-as-judge.

This module provides two modes:
1. Programmatic checks: fast, no API key, pure Python logic → EvalResult
2. LLM-as-judge: sends artifacts to an LLM for rubric scoring → EvalResult

Both modes return the same EvalResult type so tests can mix freely.

LLM routing is handled by autocritic.llm — see that module for provider
configuration and supported model strings.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Re-export LLM functions for backward compatibility with tests
from autocritic.llm import (
    _call_llm,
    _call_llm_with_image,
    _load_image,
    _parse_provider,
    _OPENAI_COMPAT_PROVIDERS,
)


@dataclass
class DimensionScore:
    dimension: str
    score: int  # 0-4
    evidence: str


@dataclass
class EvalResult:
    eval_name: str
    scores: list[DimensionScore]
    failure_evidence: list[str]
    judge_reasoning: str
    passed: bool

    @property
    def total_score(self) -> int:
        return sum(s.score for s in self.scores)

    @property
    def max_score(self) -> int:
        return len(self.scores) * 4

    def summary(self) -> str:
        lines = [f"Eval: {self.eval_name}  {'PASS' if self.passed else 'FAIL'}  "
                 f"({self.total_score}/{self.max_score})"]
        for s in self.scores:
            lines.append(f"  {s.dimension}: {s.score}/4 — {s.evidence}")
        if self.failure_evidence:
            lines.append("  Failures:")
            for f in self.failure_evidence:
                lines.append(f"    - {f}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------

def _parse_judge_response(raw: str) -> dict[str, Any]:
    """Extract JSON from an LLM response, trying multiple strategies.

    Strategy order:
    1. Fenced ```json ... ``` block
    2. Fenced ``` ... ``` block (no language tag)
    3. First bare JSON object found via brace-matching
    4. Whole response as JSON
    """
    # Strategy 1 & 2: fenced code blocks
    match = re.search(r"```(?:json)?\s*\n(.*?)\n```", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Strategy 3: find { ... } objects in the response (try each candidate)
    search_from = 0
    while True:
        start = raw.find("{", search_from)
        if start == -1:
            break
        depth = 0
        for i in range(start, len(raw)):
            if raw[i] == "{":
                depth += 1
            elif raw[i] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(raw[start : i + 1])
                    except json.JSONDecodeError:
                        pass
                    break
        search_from = start + 1

    # Strategy 4: whole response
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    raise json.JSONDecodeError("No JSON object found in LLM response", raw, 0)


def _match_dimension(dim_key: str, rubric_dimensions: list[str]) -> str | None:
    """Fuzzy-match a dimension key from the LLM response to our rubric dimensions.

    The LLM may return shortened keys like "specificity" instead of
    "specificity: directives reference visible features, not abstractions".
    We match on the prefix before the colon, or on substring containment.
    """
    dim_lower = dim_key.lower().strip()

    # Exact match first
    for dim in rubric_dimensions:
        if dim.lower() == dim_lower:
            return dim

    # Prefix match: "specificity" matches "specificity: ..."
    for dim in rubric_dimensions:
        prefix = dim.split(":")[0].strip().lower()
        if prefix == dim_lower:
            return dim

    # Substring containment: dimension key appears in rubric dimension
    for dim in rubric_dimensions:
        if dim_lower in dim.lower():
            return dim

    # Reverse: rubric prefix appears in dimension key
    for dim in rubric_dimensions:
        prefix = dim.split(":")[0].strip().lower()
        if prefix in dim_lower:
            return dim

    return None


# ---------------------------------------------------------------------------
# LLM-as-judge
# ---------------------------------------------------------------------------

def run_judge(
    eval_name: str,
    artifact_description: str,
    artifact_content: str,
    rubric_dimensions: list[str],
    failure_modes: list[str],
    pass_threshold: int,
    model: str = "claude-sonnet-4-20250514",
) -> EvalResult:
    """
    Run an LLM-as-judge evaluation.

    Args:
        eval_name: Human-readable name for this eval
        artifact_description: What is being evaluated
        artifact_content: The actual content to judge
        rubric_dimensions: List of dimension names to score (each 0-4)
        failure_modes: Known failure patterns to watch for
        pass_threshold: Minimum total score to pass

    Returns:
        EvalResult with per-dimension scores and pass/fail determination
    """
    dimensions_block = "\n".join(
        f"  {i+1}. {dim}: score 0 (absent/wrong) to 4 (excellent)"
        for i, dim in enumerate(rubric_dimensions)
    )
    failures_block = "\n".join(f"  - {fm}" for fm in failure_modes)

    # Build short keys for the JSON template so the LLM uses them
    dim_short_keys = [dim.split(":")[0].strip() for dim in rubric_dimensions]

    json_template = json.dumps({
        "dimensions": {
            key: {"score": 0, "evidence": "..."}
            for key in dim_short_keys
        },
        "failure_evidence": ["..."],
        "reasoning": "...",
    }, indent=2)

    system = (
        "You are an evaluation judge for an art-theory critic system. "
        "Your job is to score artifacts against a rubric with precision and evidence. "
        "Be strict. Generic or vague artifacts should score low. "
        "Artifacts that demonstrate specific, grounded knowledge of the theorist should score high.\n\n"
        "You MUST respond with a fenced JSON block and nothing else.\n\n"
        "```json\n"
        f"{json_template}\n"
        "```\n\n"
        "Replace each score with 0-4 and each evidence with a specific quote or observation."
    )

    user = (
        f"## Evaluating: {artifact_description}\n\n"
        f"## Rubric Dimensions\n{dimensions_block}\n\n"
        f"## Known Failure Modes (check for these specifically)\n{failures_block}\n\n"
        f"## Artifact\n{artifact_content}\n\n"
        f"Score this artifact now. Respond ONLY with the JSON block above, filled in."
    )

    raw = _call_llm(model, system, user)
    try:
        parsed = _parse_judge_response(raw)
    except json.JSONDecodeError:
        # Total parse failure — return a failing result with the raw response
        return EvalResult(
            eval_name=eval_name,
            scores=[DimensionScore(dim, 0, "JSON parse failure") for dim in rubric_dimensions],
            failure_evidence=[f"Could not parse JSON from LLM response ({len(raw)} chars)"],
            judge_reasoning=raw[:500],
            passed=False,
        )

    # Fuzzy-match dimension keys from the response to our rubric dimensions
    raw_dims = parsed.get("dimensions", {})
    scores = []
    for dim in rubric_dimensions:
        # Try exact match first, then fuzzy
        dim_data = raw_dims.get(dim, {})
        if not dim_data:
            # Try to find a matching key in the response
            for resp_key, resp_val in raw_dims.items():
                matched = _match_dimension(resp_key, [dim])
                if matched:
                    dim_data = resp_val
                    break
        scores.append(DimensionScore(
            dimension=dim,
            score=min(4, max(0, int(dim_data.get("score", 0)))) if isinstance(dim_data, dict) else 0,
            evidence=dim_data.get("evidence", "no evidence provided") if isinstance(dim_data, dict) else "no evidence provided",
        ))

    failure_evidence = parsed.get("failure_evidence", [])
    total = sum(s.score for s in scores)

    return EvalResult(
        eval_name=eval_name,
        scores=scores,
        failure_evidence=failure_evidence,
        judge_reasoning=parsed.get("reasoning", raw),
        passed=total >= pass_threshold,
    )


def run_comparative_judge(
    eval_name: str,
    description: str,
    artifact_a: str,
    artifact_b: str,
    comparison_dimensions: list[str],
    pass_threshold: int,
    model: str = "claude-sonnet-4-20250514",
) -> EvalResult:
    """
    Run a comparative eval — judge whether artifact_a is meaningfully
    different from artifact_b along the given dimensions.
    """
    dimensions_block = "\n".join(
        f"  {i+1}. {dim}: score 0 (identical) to 4 (sharply distinct)"
        for i, dim in enumerate(comparison_dimensions)
    )

    # Build short keys for the JSON template
    dim_short_keys = [dim.split(":")[0].strip() for dim in comparison_dimensions]

    json_template = json.dumps({
        "dimensions": {
            key: {"score": 0, "evidence": "..."}
            for key in dim_short_keys
        },
        "failure_evidence": ["..."],
        "reasoning": "...",
    }, indent=2)

    system = (
        "You are an evaluation judge comparing two artifacts for meaningful "
        "difference. Score how DISTINCT artifact A is from artifact B along "
        "each dimension. High scores mean A says things B could never say. "
        "Low scores mean A could be swapped for B without anyone noticing.\n\n"
        "You MUST respond with a fenced JSON block and nothing else.\n\n"
        "```json\n"
        f"{json_template}\n"
        "```\n\n"
        "Replace each score with 0-4 and each evidence with a specific quote or observation."
    )

    user = (
        f"## Comparison: {description}\n\n"
        f"## Dimensions of Distinction\n{dimensions_block}\n\n"
        f"## Artifact A\n{artifact_a}\n\n"
        f"## Artifact B\n{artifact_b}\n\n"
        f"Score how distinct A is from B. Respond ONLY with the JSON block above, filled in."
    )

    raw = _call_llm(model, system, user)
    try:
        parsed = _parse_judge_response(raw)
    except json.JSONDecodeError:
        return EvalResult(
            eval_name=eval_name,
            scores=[DimensionScore(dim, 0, "JSON parse failure") for dim in comparison_dimensions],
            failure_evidence=[f"Could not parse JSON from LLM response ({len(raw)} chars)"],
            judge_reasoning=raw[:500],
            passed=False,
        )

    # Fuzzy-match dimension keys
    raw_dims = parsed.get("dimensions", {})
    scores = []
    for dim in comparison_dimensions:
        dim_data = raw_dims.get(dim, {})
        if not dim_data:
            for resp_key, resp_val in raw_dims.items():
                matched = _match_dimension(resp_key, [dim])
                if matched:
                    dim_data = resp_val
                    break
        scores.append(DimensionScore(
            dimension=dim,
            score=min(4, max(0, int(dim_data.get("score", 0)))) if isinstance(dim_data, dict) else 0,
            evidence=dim_data.get("evidence", "no evidence provided") if isinstance(dim_data, dict) else "no evidence provided",
        ))

    failure_evidence = parsed.get("failure_evidence", [])
    total = sum(s.score for s in scores)

    return EvalResult(
        eval_name=eval_name,
        scores=scores,
        failure_evidence=failure_evidence,
        judge_reasoning=parsed.get("reasoning", raw),
        passed=total >= pass_threshold,
    )


# ---------------------------------------------------------------------------
# Programmatic checks (no API key needed)
# ---------------------------------------------------------------------------

def run_programmatic_check(
    eval_name: str,
    checks: list[tuple[str, bool, str]],
) -> EvalResult:
    """
    Run a set of boolean checks and return a unified EvalResult.

    Each check is (dimension_name, passed: bool, evidence: str).
    A passing check scores 4; a failing check scores 0.
    The overall eval passes only if ALL checks pass.
    """
    scores = [
        DimensionScore(
            dimension=name,
            score=4 if passed else 0,
            evidence=evidence,
        )
        for name, passed, evidence in checks
    ]
    failures = [s.evidence for s in scores if s.score == 0]
    return EvalResult(
        eval_name=eval_name,
        scores=scores,
        failure_evidence=failures,
        judge_reasoning="programmatic check",
        passed=len(failures) == 0,
    )


def run_vocabulary_check(
    eval_name: str,
    text: str,
    distinctive_vocab: list[str],
    generic_vocab: list[str] | None = None,
    min_distinctive_ratio: float = 0.4,
) -> EvalResult:
    """
    Check that an artifact uses enough distinctive vocabulary and isn't
    dominated by generic terms.
    """
    text_lower = text.lower()
    distinctive_hits = [v for v in distinctive_vocab if v.lower() in text_lower]
    ratio = len(distinctive_hits) / len(distinctive_vocab) if distinctive_vocab else 0

    checks: list[tuple[str, bool, str]] = [
        (
            "distinctive_coverage",
            ratio >= min_distinctive_ratio,
            f"{len(distinctive_hits)}/{len(distinctive_vocab)} ({ratio:.0%}) distinctive terms found"
            + (f". Missing: {set(v.lower() for v in distinctive_vocab) - set(v.lower() for v in distinctive_hits)}"
               if ratio < min_distinctive_ratio else ""),
        ),
    ]

    if generic_vocab is not None:
        generic_hits = sum(1 for v in generic_vocab if v.lower() in text_lower)
        checks.append((
            "generic_dominance",
            len(distinctive_hits) >= generic_hits,
            f"distinctive={len(distinctive_hits)} vs generic={generic_hits}",
        ))

    return run_programmatic_check(eval_name, checks)


def run_structural_check(
    eval_name: str,
    card: dict,
    required_top_level: list[str],
    criteria_key: str = "criteria",
    required_criteria_fields: list[str] | None = None,
    min_criteria: int = 1,
) -> EvalResult:
    """
    Validate the shape of a critic card.
    """
    checks: list[tuple[str, bool, str]] = []

    missing_top = [f for f in required_top_level if f not in card]
    checks.append((
        "top_level_fields",
        len(missing_top) == 0,
        f"missing: {missing_top}" if missing_top else f"all {len(required_top_level)} fields present",
    ))

    items = card.get(criteria_key, [])
    checks.append((
        f"{criteria_key}_count",
        len(items) >= min_criteria,
        f"found {len(items)}, need >= {min_criteria}",
    ))

    if required_criteria_fields and items:
        bad = []
        for item in items:
            item_id = item.get("element_id", item.get("criterion_id", "?"))
            missing = [f for f in required_criteria_fields if f not in item]
            if missing:
                bad.append(f"{item_id} missing {missing}")
        checks.append((
            "criteria_fields",
            len(bad) == 0,
            "; ".join(bad) if bad else "all criteria have required fields",
        ))

    return run_programmatic_check(eval_name, checks)
