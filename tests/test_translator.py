"""Tests for the translator module: ParamSpace, apply_deltas, translation."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from autocritic.scoring import AxisScore, ScoredCritique
from autocritic.critic import CritiqueResult
from autocritic.translator import (
    ParamSpec,
    ParamSpace,
    TranslationResult,
    apply_deltas,
    translate_critique_to_params,
    _parse_translation,
)


# ---------------------------------------------------------------------------
# ParamSpace
# ---------------------------------------------------------------------------

SAMPLE_SPACE = ParamSpace(specs=[
    ParamSpec("speed", "float", (0.0, 10.0), 5.0, "Movement speed"),
    ParamSpec("count", "int", (1, 100), 10, "Number of items"),
    ParamSpec("mode", "enum", ("fast", "slow", "balanced"), "balanced", "Operation mode"),
    ParamSpec("label", "string", (), "", "Descriptive label"),
])


class TestParamSpace:
    def test_defaults(self):
        d = SAMPLE_SPACE.defaults()
        assert d == {"speed": 5.0, "count": 10, "mode": "balanced", "label": ""}

    def test_describe_format(self):
        desc = SAMPLE_SPACE.describe()
        assert "speed" in desc
        assert "count" in desc
        assert "mode" in desc
        assert "label" in desc
        assert "range:" in desc
        assert "options:" in desc
        assert "free-text" in desc

    def test_clamp_float_high(self):
        result = SAMPLE_SPACE.clamp({"speed": 15.0, "count": 10, "mode": "fast"})
        assert result["speed"] == 10.0

    def test_clamp_float_low(self):
        result = SAMPLE_SPACE.clamp({"speed": -5.0, "count": 10, "mode": "fast"})
        assert result["speed"] == 0.0

    def test_clamp_int(self):
        result = SAMPLE_SPACE.clamp({"speed": 5.0, "count": 200, "mode": "fast"})
        assert result["count"] == 100

    def test_clamp_enum_invalid(self):
        result = SAMPLE_SPACE.clamp({"speed": 5.0, "count": 10, "mode": "invalid"})
        assert result["mode"] == "balanced"  # reset to default

    def test_clamp_enum_valid(self):
        result = SAMPLE_SPACE.clamp({"speed": 5.0, "count": 10, "mode": "fast"})
        assert result["mode"] == "fast"

    def test_clamp_string_passthrough(self):
        result = SAMPLE_SPACE.clamp({"speed": 5.0, "count": 10, "mode": "fast", "label": "anything goes"})
        assert result["label"] == "anything goes"


# ---------------------------------------------------------------------------
# apply_deltas
# ---------------------------------------------------------------------------

class TestApplyDeltas:
    def test_full_damping(self):
        current = {"speed": 5.0, "count": 10, "mode": "balanced", "label": ""}
        deltas = {"speed": 8.0}
        result = apply_deltas(current, deltas, SAMPLE_SPACE, damping=1.0)
        assert result["speed"] == 8.0

    def test_half_damping(self):
        current = {"speed": 5.0, "count": 10, "mode": "balanced", "label": ""}
        deltas = {"speed": 9.0}
        result = apply_deltas(current, deltas, SAMPLE_SPACE, damping=0.5)
        # 5.0 + 0.5 * (9.0 - 5.0) = 7.0
        assert result["speed"] == pytest.approx(7.0)

    def test_enum_ignores_damping(self):
        current = {"speed": 5.0, "count": 10, "mode": "balanced", "label": ""}
        deltas = {"mode": "fast"}
        result = apply_deltas(current, deltas, SAMPLE_SPACE, damping=0.5)
        assert result["mode"] == "fast"

    def test_clamped_after_apply(self):
        current = {"speed": 9.0, "count": 10, "mode": "balanced", "label": ""}
        deltas = {"speed": 15.0}
        result = apply_deltas(current, deltas, SAMPLE_SPACE, damping=1.0)
        assert result["speed"] == 10.0

    def test_int_rounded(self):
        current = {"speed": 5.0, "count": 10, "mode": "balanced", "label": ""}
        deltas = {"count": 15}
        result = apply_deltas(current, deltas, SAMPLE_SPACE, damping=0.7)
        # 10 + 0.7 * (15 - 10) = 13.5 → rounds to 14
        assert result["count"] == 14
        assert isinstance(result["count"], int)

    def test_unknown_param_ignored(self):
        current = {"speed": 5.0, "count": 10, "mode": "balanced", "label": ""}
        deltas = {"nonexistent": 42}
        result = apply_deltas(current, deltas, SAMPLE_SPACE, damping=1.0)
        assert "nonexistent" not in result

    def test_empty_deltas(self):
        current = {"speed": 5.0, "count": 10, "mode": "balanced", "label": ""}
        result = apply_deltas(current, {}, SAMPLE_SPACE, damping=1.0)
        assert result == current

    def test_string_set_directly(self):
        current = {"speed": 5.0, "count": 10, "mode": "balanced", "label": "old"}
        deltas = {"label": "new label text"}
        result = apply_deltas(current, deltas, SAMPLE_SPACE, damping=0.3)
        assert result["label"] == "new label text"  # damping ignored for strings


# ---------------------------------------------------------------------------
# _parse_translation
# ---------------------------------------------------------------------------

class TestParseTranslation:
    def test_fenced_json(self):
        raw = 'Some reasoning.\n\n```json\n{"deltas": {"speed": 7.0}, "reasoning": "Increase speed"}\n```'
        deltas, reasoning = _parse_translation(raw)
        assert deltas == {"speed": 7.0}
        assert reasoning == "Increase speed"

    def test_no_json_raises(self):
        from autocritic.translator import TranslationParseError
        with pytest.raises(TranslationParseError, match="No fenced"):
            _parse_translation("No JSON here.")

    def test_invalid_json_raises(self):
        from autocritic.translator import TranslationParseError
        with pytest.raises(TranslationParseError, match="Invalid JSON"):
            _parse_translation('```json\n{broken\n```')


# ---------------------------------------------------------------------------
# translate_critique_to_params (mocked LLM)
# ---------------------------------------------------------------------------

MOCK_TRANSLATION_RESPONSE = """
I'll analyze the critique and suggest parameter changes.

The critique indicates the drawing is too dense and lacks spatial variation.
To address this:

```json
{
  "deltas": {"speed": 7.5, "mode": "fast"},
  "reasoning": "Increasing speed and switching to fast mode to create more spatial variation."
}
```
"""


class TestTranslateCritiqueToParams:
    def test_mocked_translation(self):
        critique = CritiqueResult(
            critic_id="test", image_path="img.png", model="test",
            raw_text="raw", directives=["Make it sparser"],
            strengths=["Good contours"],
            weaknesses=["Too dense"],
        )
        scored = ScoredCritique(
            critique=critique,
            axis_scores=[AxisScore("a", "A", 0.3, "moderate")],
            composite_score=0.3,
        )

        with patch(
            "autocritic.llm._call_llm",
            return_value=MOCK_TRANSLATION_RESPONSE,
        ):
            result = translate_critique_to_params(
                scored,
                {"speed": 5.0, "count": 10, "mode": "balanced", "label": ""},
                SAMPLE_SPACE,
                model="test",
            )

        assert isinstance(result, TranslationResult)
        assert result.deltas == {"speed": 7.5, "mode": "fast"}
        assert "spatial variation" in result.reasoning
