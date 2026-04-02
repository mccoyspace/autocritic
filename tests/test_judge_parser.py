"""
Tests for the LLM-as-judge response parser and dimension matching.

These are pure unit tests — no API calls.
"""

from __future__ import annotations

import json

import pytest

from evals.judge import _match_dimension, _parse_judge_response


# ---------------------------------------------------------------------------
# _parse_judge_response
# ---------------------------------------------------------------------------

class TestParseJudgeResponse:
    def test_fenced_json(self):
        raw = '```json\n{"dimensions": {}, "reasoning": "ok"}\n```'
        result = _parse_judge_response(raw)
        assert result["reasoning"] == "ok"

    def test_fenced_no_language_tag(self):
        raw = '```\n{"dimensions": {}, "reasoning": "ok"}\n```'
        result = _parse_judge_response(raw)
        assert result["reasoning"] == "ok"

    def test_prose_then_json(self):
        """GPT-5.4 often writes prose before/after JSON."""
        raw = (
            "Here is my evaluation of the artifact:\n\n"
            '{"dimensions": {"specificity": {"score": 3, "evidence": "good"}}, '
            '"failure_evidence": [], "reasoning": "solid"}\n\n'
            "I hope this helps with your evaluation."
        )
        result = _parse_judge_response(raw)
        assert result["dimensions"]["specificity"]["score"] == 3

    def test_bare_json_no_prose(self):
        raw = '{"dimensions": {}, "reasoning": "ok"}'
        result = _parse_judge_response(raw)
        assert result["reasoning"] == "ok"

    def test_nested_braces(self):
        raw = (
            'Some text {"dimensions": {"a": {"score": 2, "evidence": "b"}}, '
            '"failure_evidence": [], "reasoning": "c"} more text'
        )
        result = _parse_judge_response(raw)
        assert result["dimensions"]["a"]["score"] == 2

    def test_fenced_json_with_surrounding_prose(self):
        raw = (
            "I'll evaluate this now.\n\n"
            "```json\n"
            '{"dimensions": {"x": {"score": 4, "evidence": "great"}}, '
            '"failure_evidence": [], "reasoning": "excellent"}\n'
            "```\n\n"
            "That concludes my evaluation."
        )
        result = _parse_judge_response(raw)
        assert result["dimensions"]["x"]["score"] == 4

    def test_pure_prose_raises(self):
        raw = (
            "The artifact demonstrates strong theoretical grounding. "
            "The specificity is excellent with clear references to visual features. "
            "The directionality is also strong."
        )
        with pytest.raises(json.JSONDecodeError):
            _parse_judge_response(raw)

    def test_malformed_json_in_fence_falls_through_to_bare(self):
        raw = (
            '```json\n{not valid json}\n```\n\n'
            '{"dimensions": {}, "reasoning": "fallback"}'
        )
        result = _parse_judge_response(raw)
        assert result["reasoning"] == "fallback"


# ---------------------------------------------------------------------------
# _match_dimension
# ---------------------------------------------------------------------------

class TestMatchDimension:
    def test_exact_match(self):
        dims = ["specificity: directives reference visible features"]
        assert _match_dimension("specificity: directives reference visible features", dims) == dims[0]

    def test_prefix_match(self):
        dims = ["specificity: directives reference visible features, not abstractions"]
        assert _match_dimension("specificity", dims) == dims[0]

    def test_prefix_match_case_insensitive(self):
        dims = ["Specificity: directives reference visible features"]
        assert _match_dimension("specificity", dims) == dims[0]

    def test_substring_match(self):
        dims = ["distinctive vocabulary: uses theorist-specific terms"]
        assert _match_dimension("distinctive vocabulary", dims) == dims[0]

    def test_reverse_prefix_match(self):
        dims = ["specificity: directives reference visible features"]
        assert _match_dimension("specificity of directives", dims) == dims[0]

    def test_no_match(self):
        dims = ["specificity: directives reference visible features"]
        assert _match_dimension("completely_unrelated", dims) is None

    def test_multiple_dims_correct_match(self):
        dims = [
            "specificity: directives reference visible features",
            "directionality: each directive implies a clear change direction",
            "non-contradiction: directives do not work against each other",
        ]
        assert _match_dimension("directionality", dims) == dims[1]
        assert _match_dimension("non-contradiction", dims) == dims[2]
