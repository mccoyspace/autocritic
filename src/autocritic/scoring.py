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

from autocritic.critic import (
    CriticCard,
    CritiqueResult,
    _build_system_prompt,
    _extract_bullet_list,
    _extract_criterion_notes,
    _parse_critique,
)


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
    all_items = critic.all_items
    for item in all_items:
        # Find the appropriate id field for this item
        item_id = "unknown"
        for idf in ("criterion_id", "concept_id", "element_id", "impulse_id", "principle_id", "dimension_id", "id"):
            if idf in item:
                item_id = item[idf]
                break
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
        # Try unfenced JSON at end of response
        pattern2 = r"\{[^{}]*\"axis_scores\"[^{}]*\[.*?\]\s*\}"
        matches = re.findall(pattern2, raw_text, re.DOTALL)

    if not matches:
        return []

    # Use the last match (scoring block comes after critique)
    raw_json = matches[-1].strip()
    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError:
        return []

    scores_data = data.get("axis_scores", [])
    if not isinstance(scores_data, list):
        return []

    # Build label lookup from all items (primary + secondary)
    label_map = {}
    for item in critic.all_items:
        for idf in ("criterion_id", "concept_id", "element_id", "impulse_id", "principle_id", "dimension_id", "id"):
            if idf in item:
                label_map[item[idf]] = item.get("label", item[idf])
                break

    scores = []
    for entry in scores_data:
        axis_id = entry.get("axis_id", "")
        scores.append(AxisScore(
            axis_id=axis_id,
            label=label_map.get(axis_id, axis_id),
            score=float(entry.get("score", 0.0)),
            reasoning=str(entry.get("reasoning", "")),
        ))

    return scores


def compute_composite_score(
    axis_scores: list[AxisScore],
    bipolar: bool,
) -> float:
    """Compute a 0-1 composite score from axis scores.

    For bipolar axes: abs(score) measures commitment to either pole.
    For unipolar axes: score is already 0-1.
    """
    if not axis_scores:
        return 0.0

    values = []
    for s in axis_scores:
        if bipolar:
            values.append(abs(s.score))
        else:
            values.append(max(0.0, min(1.0, s.score)))

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
    """Compute improvement delta: positive means b is better than a."""
    return b.composite_score - a.composite_score
