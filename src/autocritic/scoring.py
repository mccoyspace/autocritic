"""
Scored critique: extends critique_image with numeric axis scores.

Produces a ScoredCritique that combines the qualitative CritiqueResult
with per-axis numeric positions, enabling quantitative comparison
across iterations.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class ScoreParseError(ValueError):
    """Raised when axis score JSON cannot be parsed from LLM output."""

    def __init__(self, message: str, raw_text: str = ""):
        super().__init__(message)
        self.raw_text = raw_text

from autocritic.critic import (
    CriticCard,
    CritiqueResult,
    _ID_FIELDS,
    _build_system_prompt,
    _extract_bullet_list,
    _extract_criterion_notes,
    _parse_critique,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ID_FIELD_CANDIDATES = tuple(_ID_FIELDS) + ("id",)


def _get_item_id(item: dict[str, Any]) -> str:
    """Return the ID value from an item dict, checking known ID fields."""
    for idf in _ID_FIELD_CANDIDATES:
        if idf in item:
            return item[idf]
    return "unknown"


def _expected_axis_ids(critic: CriticCard) -> dict[str, str]:
    """Build {axis_id: label} for all expected axes in a critic card."""
    mapping: dict[str, str] = {}
    for item in critic.all_items:
        axis_id = _get_item_id(item)
        mapping[axis_id] = item.get("label", axis_id)
    return mapping


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class AxisScore:
    """Numeric position on a single theoretical axis."""
    axis_id: str       # matches item_id_field value
    label: str         # human-readable label
    score: float       # -1.0 to +1.0 (bipolar) or 0.0 to 1.0 (unipolar)
    reasoning: str     # one-line justification


@dataclass
class ScoredCritique:
    """Qualitative critique plus numeric axis scores."""
    critique: CritiqueResult
    axis_scores: list[AxisScore] = field(default_factory=list)
    composite_score: float = 0.0

    def score_for(self, axis_id: str) -> AxisScore | None:
        """Look up a specific axis score by ID."""
        for s in self.axis_scores:
            if s.axis_id == axis_id:
                return s
        return None


# ---------------------------------------------------------------------------
# Bipolar detection
# ---------------------------------------------------------------------------

def is_bipolar(critic: CriticCard) -> bool:
    """Detect whether a critic card uses bipolar axes (pole_a/pole_b).

    Checks the explicit ``scoring_mode`` field first (preferred).
    Falls back to inspecting ALL items for pole_a/pole_b indicators,
    asserting consistency across the card.
    """
    # Prefer explicit field
    mode = critic.raw.get("scoring_mode")
    if mode is not None:
        return mode == "bipolar"

    # Heuristic: check all items for consistency
    if not critic.items:
        return False
    item_polarities = []
    for item in critic.items:
        indicators = item.get("indicators", {})
        has_poles = "pole_a" in indicators and "pole_b" in indicators
        item_polarities.append(has_poles)

    if all(item_polarities):
        return True
    if not any(item_polarities):
        return False
    # Mixed — some items bipolar, some not. Flag the inconsistency.
    raise ValueError(
        f"Critic card '{critic.critic_id}' has mixed indicator structures: "
        f"some items have pole_a/pole_b, others don't. "
        f"Add an explicit \"scoring_mode\": \"bipolar\" or \"unipolar\" to the card."
    )


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------

def build_scoring_prompt_section(critic: CriticCard) -> str:
    """Build the axis-scoring instruction appended to the critique prompt.

    Asks the LLM to output a JSON block with a numeric score for each axis.
    """
    bipolar = is_bipolar(critic)

    lines = [
        "",
        "## Axis Scores",
        "After your critique above, output a JSON block scoring each axis.",
        "",
    ]

    if bipolar:
        lines.append(
            "For each axis, score from **-1.0** (strongly pole A) "
            "through **0.0** (neutral/indeterminate) to **+1.0** (strongly pole B). "
            "A high absolute value means the image clearly commits to one pole. "
            "A score near 0 means the image is ambiguous or mixed on that axis."
        )
    else:
        lines.append(
            "For each axis, score from **0.0** (weak/absent presence of this quality) "
            "to **1.0** (strong/masterful presence). "
            "A score of 0.5 means moderate presence."
        )

    lines.extend([
        "",
        "Score these axes:",
    ])

    # Score all items: primary + secondary
    for item in critic.all_items:
        item_id = _get_item_id(item)
        label = item.get("label", item_id)
        if bipolar:
            pole_a = item.get("indicators", {}).get("pole_a", [""])[0] if item.get("indicators") else ""
            pole_b = item.get("indicators", {}).get("pole_b", [""])[0] if item.get("indicators") else ""
            lines.append(f"- **{item_id}** ({label}): -1.0 = {pole_a[:60]}… / +1.0 = {pole_b[:60]}…")
        else:
            lines.append(f"- **{item_id}** ({label})")

    lines.extend([
        "",
        "Output exactly this format (no other text after the JSON block):",
        "",
        "```json",
        "{",
        '  "axis_scores": [',
        '    {"axis_id": "...", "score": 0.0, "reasoning": "one sentence"}',
        "  ]",
        "}",
        "```",
    ])

    return "\n".join(lines)


def _build_scored_user_prompt(
    critic: CriticCard,
    intent: str | None = None,
) -> str:
    """Build the full user prompt: critique sections + scoring section."""
    from autocritic.critic import _build_critique_user_prompt

    base = _build_critique_user_prompt(intent)
    scoring = build_scoring_prompt_section(critic)
    return base + "\n" + scoring


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def parse_axis_scores(
    raw_text: str,
    critic: CriticCard,
) -> list[AxisScore]:
    """Extract axis scores from the JSON block in an LLM response.

    Looks for the last fenced ```json``` block in the text.
    """
    # Find all fenced JSON blocks
    pattern = r"```json\s*\n(.*?)```"
    matches = re.findall(pattern, raw_text, re.DOTALL)

    if not matches:
        raise ScoreParseError(
            "No fenced ```json``` block found in LLM response",
            raw_text=raw_text,
        )

    # Use the last match (scoring block comes after critique)
    raw_json = matches[-1].strip()
    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError as e:
        raise ScoreParseError(
            f"Invalid JSON in axis scores block: {e}",
            raw_text=raw_text,
        ) from e

    scores_data = data.get("axis_scores", [])
    if not isinstance(scores_data, list):
        raise ScoreParseError(
            f"Expected 'axis_scores' to be a list, got {type(scores_data).__name__}",
            raw_text=raw_text,
        )

    # Build expected axis set from critic card
    expected = _expected_axis_ids(critic)
    bipolar = is_bipolar(critic)

    # Parse returned scores, checking for unknown and duplicate IDs
    scores = []
    seen_ids: set[str] = set()
    for entry in scores_data:
        axis_id = entry.get("axis_id", "")
        if axis_id in seen_ids:
            raise ScoreParseError(
                f"Duplicate axis_id in response: '{axis_id}'",
                raw_text=raw_text,
            )
        seen_ids.add(axis_id)
        if axis_id not in expected:
            raise ScoreParseError(
                f"Unknown axis_id '{axis_id}' — expected one of: {sorted(expected.keys())}",
                raw_text=raw_text,
            )
        score = float(entry.get("score", 0.0))
        if bipolar and not (-1.0 <= score <= 1.0):
            raise ScoreParseError(
                f"Bipolar score out of range for '{axis_id}': {score} "
                f"(must be -1.0 to 1.0)",
                raw_text=raw_text,
            )
        if not bipolar and not (0.0 <= score <= 1.0):
            raise ScoreParseError(
                f"Unipolar score out of range for '{axis_id}': {score} "
                f"(must be 0.0 to 1.0)",
                raw_text=raw_text,
            )
        scores.append(AxisScore(
            axis_id=axis_id,
            label=expected.get(axis_id, axis_id),
            score=score,
            reasoning=str(entry.get("reasoning", "")),
        ))

    # Check for missing axes
    missing = set(expected.keys()) - seen_ids
    if missing:
        raise ScoreParseError(
            f"Missing axis scores: {sorted(missing)} "
            f"(got {len(scores)}/{len(expected)})",
            raw_text=raw_text,
        )

    return scores


def compute_composite_score(
    axis_scores: list[AxisScore],
    bipolar: bool,
) -> float:
    """Compute a 0-1 composite score from axis scores.

    For bipolar axes: abs(score) measures pole commitment, not quality.
    For unipolar axes: score is already 0-1.

    Score ranges are enforced at parse time, so values are guaranteed
    to be in [-1, 1] (bipolar) or [0, 1] (unipolar).
    """
    if not axis_scores:
        return 0.0

    if bipolar:
        values = [abs(s.score) for s in axis_scores]
    else:
        values = [s.score for s in axis_scores]

    return sum(values) / len(values)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def score_critique(
    critic: CriticCard,
    image_path: str | Path,
    model: str = "claude-sonnet-4-20250514",
    intent: str | None = None,
) -> ScoredCritique:
    """Critique an image and produce numeric axis scores in one LLM call.

    Combines the qualitative critique (CritiqueResult) with per-axis
    numeric positions (AxisScore) in a single vision call.
    """
    from autocritic.llm import _call_llm_with_image

    system = _build_system_prompt(critic)
    user = _build_scored_user_prompt(critic, intent)

    raw = _call_llm_with_image(
        model=model,
        system=system,
        user=user,
        image_path=image_path,
        max_tokens=4096,
        temperature=0.0,
    )

    # Parse the qualitative sections
    sections = _parse_critique(raw)
    critique = CritiqueResult(
        critic_id=critic.critic_id,
        image_path=str(image_path),
        model=model,
        raw_text=raw,
        lens_summary=sections.get("Lens Summary", ""),
        strengths=_extract_bullet_list(
            sections.get("Strengths To Preserve", "")
        ),
        weaknesses=_extract_bullet_list(
            sections.get("Weaknesses To Address", "")
        ),
        criterion_notes=_extract_criterion_notes(
            sections.get("Criterion Notes", "")
        ),
        directives=_extract_bullet_list(
            sections.get("Next Iteration Directives", "")
        ),
    )

    # Parse the numeric scores
    bipolar = is_bipolar(critic)
    axis_scores = parse_axis_scores(raw, critic)
    composite = compute_composite_score(axis_scores, bipolar)

    return ScoredCritique(
        critique=critique,
        axis_scores=axis_scores,
        composite_score=composite,
    )


def compare_scores(a: ScoredCritique, b: ScoredCritique) -> float:
    """Compute composite score delta: ``b.composite - a.composite``.

    For unipolar critics, positive means b scored higher (better).
    For bipolar critics, this measures change in pole commitment,
    not quality — a positive delta means stronger commitment, not
    necessarily improvement.
    """
    return b.composite_score - a.composite_score
