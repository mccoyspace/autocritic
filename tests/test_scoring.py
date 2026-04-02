"""Tests for the scoring module: axis scores, composite scores, prompt construction."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from autocritic.critic import CriticCard, load_critic
from autocritic.scoring import (
    AxisScore,
    ScoreParseError,
    ScoredCritique,
    build_scoring_prompt_section,
    compare_scores,
    compute_composite_score,
    is_bipolar,
    parse_axis_scores,
    score_critique,
)

CRITICS_DIR = Path(__file__).parent.parent / "critics"


# ---------------------------------------------------------------------------
# Bipolar detection
# ---------------------------------------------------------------------------

class TestIsBipolar:
    def test_wolfflin_is_bipolar(self):
        c = load_critic(CRITICS_DIR / "wolfflin.json")
        assert is_bipolar(c) is True

    def test_kandinsky_is_not_bipolar(self):
        c = load_critic(CRITICS_DIR / "kandinsky.json")
        assert is_bipolar(c) is False

    def test_dow_is_not_bipolar(self):
        c = load_critic(CRITICS_DIR / "dow.json")
        assert is_bipolar(c) is False

    def test_arnheim_is_not_bipolar(self):
        c = load_critic(CRITICS_DIR / "arnheim.json")
        assert is_bipolar(c) is False


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------

class TestBuildScoringPromptSection:
    def test_bipolar_prompt_has_pole_instructions(self):
        c = load_critic(CRITICS_DIR / "wolfflin.json")
        prompt = build_scoring_prompt_section(c)
        assert "-1.0" in prompt
        assert "+1.0" in prompt
        assert "pole A" in prompt or "pole_a" in prompt.lower()
        assert "axis_scores" in prompt

    def test_unipolar_prompt_has_01_range(self):
        c = load_critic(CRITICS_DIR / "dow.json")
        prompt = build_scoring_prompt_section(c)
        assert "0.0" in prompt
        assert "1.0" in prompt
        assert "-1.0" not in prompt  # no bipolar range
        assert "axis_scores" in prompt

    def test_prompt_lists_all_axes(self):
        c = load_critic(CRITICS_DIR / "wolfflin.json")
        prompt = build_scoring_prompt_section(c)
        for item in c.items:
            item_id = item[c.item_id_field]
            assert item_id in prompt

    def test_prompt_lists_all_unipolar_axes(self):
        c = load_critic(CRITICS_DIR / "kandinsky.json")
        prompt = build_scoring_prompt_section(c)
        for item in c.items:
            item_id = item[c.item_id_field]
            assert item_id in prompt


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

SAMPLE_RESPONSE_WITH_SCORES = """## Lens Summary
Linear-painterly axis dominates.

## Strengths To Preserve
- Strong contours throughout

## Weaknesses To Address
- Lacks depth variation

## Criterion Notes
### Linear vs Painterly
Strongly linear.

## Next Iteration Directives
- Soften edges in shadow areas

## Axis Scores

```json
{
  "axis_scores": [
    {"axis_id": "linear_painterly", "score": -0.7, "reasoning": "Strong contours, no tonal merging"},
    {"axis_id": "plane_recession", "score": -0.3, "reasoning": "Mostly planar arrangement"},
    {"axis_id": "closed_open", "score": 0.4, "reasoning": "Some elements extend past frame"},
    {"axis_id": "multiplicity_unity", "score": 0.2, "reasoning": "Slight unity tendency"},
    {"axis_id": "clearness_unclearness", "score": -0.5, "reasoning": "Forms clearly presented"}
  ]
}
```
"""


class TestParseAxisScores:
    def test_parses_fenced_json(self):
        c = load_critic(CRITICS_DIR / "wolfflin.json")
        scores = parse_axis_scores(SAMPLE_RESPONSE_WITH_SCORES, c)
        assert len(scores) == 5
        assert scores[0].axis_id == "linear_painterly"
        assert scores[0].score == -0.7

    def test_scores_have_reasoning(self):
        c = load_critic(CRITICS_DIR / "wolfflin.json")
        scores = parse_axis_scores(SAMPLE_RESPONSE_WITH_SCORES, c)
        assert all(s.reasoning for s in scores)

    def test_empty_response_raises(self):
        c = load_critic(CRITICS_DIR / "wolfflin.json")
        with pytest.raises(ScoreParseError, match="No fenced"):
            parse_axis_scores("No JSON here.", c)

    def test_invalid_json_raises(self):
        c = load_critic(CRITICS_DIR / "wolfflin.json")
        with pytest.raises(ScoreParseError, match="Invalid JSON"):
            parse_axis_scores("```json\n{broken\n```", c)

    def test_missing_axes_raises(self):
        """Incomplete axis set should raise, not silently average a subset."""
        c = load_critic(CRITICS_DIR / "wolfflin.json")
        partial = '```json\n{"axis_scores": [{"axis_id": "linear_painterly", "score": 1.0, "reasoning": "x"}]}\n```'
        with pytest.raises(ScoreParseError, match="Missing axis scores"):
            parse_axis_scores(partial, c)

    def test_unknown_axis_id_raises(self):
        c = load_critic(CRITICS_DIR / "wolfflin.json")
        bad_id = '```json\n{"axis_scores": [{"axis_id": "made_up", "score": 0.5, "reasoning": "x"}]}\n```'
        with pytest.raises(ScoreParseError, match="Unknown axis_id"):
            parse_axis_scores(bad_id, c)

    def test_duplicate_axis_id_raises(self):
        c = load_critic(CRITICS_DIR / "wolfflin.json")
        duped = (
            '```json\n{"axis_scores": ['
            '{"axis_id": "linear_painterly", "score": 0.5, "reasoning": "x"},'
            '{"axis_id": "linear_painterly", "score": 0.3, "reasoning": "y"}'
            ']}\n```'
        )
        with pytest.raises(ScoreParseError, match="Duplicate"):
            parse_axis_scores(duped, c)


# ---------------------------------------------------------------------------
# Composite score
# ---------------------------------------------------------------------------

class TestCompositeScore:
    def test_bipolar_uses_abs(self):
        scores = [
            AxisScore("a", "A", -0.8, ""),
            AxisScore("b", "B", 0.6, ""),
        ]
        composite = compute_composite_score(scores, bipolar=True)
        assert abs(composite - 0.7) < 0.01  # avg(0.8, 0.6) = 0.7

    def test_unipolar_direct(self):
        scores = [
            AxisScore("a", "A", 0.8, ""),
            AxisScore("b", "B", 0.6, ""),
        ]
        composite = compute_composite_score(scores, bipolar=False)
        assert abs(composite - 0.7) < 0.01

    def test_empty_returns_zero(self):
        assert compute_composite_score([], bipolar=True) == 0.0

    def test_unipolar_clamps(self):
        scores = [AxisScore("a", "A", 1.5, "")]
        composite = compute_composite_score(scores, bipolar=False)
        assert composite == 1.0


# ---------------------------------------------------------------------------
# Compare scores
# ---------------------------------------------------------------------------

class TestCompareScores:
    def test_positive_means_improvement(self):
        a = ScoredCritique(critique=None, axis_scores=[], composite_score=0.4)
        b = ScoredCritique(critique=None, axis_scores=[], composite_score=0.6)
        assert compare_scores(a, b) == pytest.approx(0.2)

    def test_negative_means_regression(self):
        a = ScoredCritique(critique=None, axis_scores=[], composite_score=0.6)
        b = ScoredCritique(critique=None, axis_scores=[], composite_score=0.4)
        assert compare_scores(a, b) == pytest.approx(-0.2)


# ---------------------------------------------------------------------------
# ScoredCritique
# ---------------------------------------------------------------------------

class TestScoredCritique:
    def test_score_for_existing(self):
        sc = ScoredCritique(
            critique=None,
            axis_scores=[AxisScore("a", "A", 0.5, "reason")],
            composite_score=0.5,
        )
        assert sc.score_for("a").score == 0.5

    def test_score_for_missing(self):
        sc = ScoredCritique(critique=None, axis_scores=[], composite_score=0.0)
        assert sc.score_for("nonexistent") is None


# ---------------------------------------------------------------------------
# score_critique (mocked LLM)
# ---------------------------------------------------------------------------

class TestScoreCritiqueMocked:
    def test_returns_scored_critique(self):
        c = load_critic(CRITICS_DIR / "wolfflin.json")
        image = Path(__file__).parent / "fixtures" / "test_image.png"

        with patch(
            "autocritic.llm._call_llm_with_image",
            return_value=SAMPLE_RESPONSE_WITH_SCORES,
        ):
            result = score_critique(c, image, model="test")

        assert isinstance(result, ScoredCritique)
        assert result.critique.critic_id == "wolfflin"
        assert len(result.axis_scores) == 5
        assert result.composite_score > 0
