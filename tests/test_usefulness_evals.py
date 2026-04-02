"""
Tests for the usefulness eval module.

Uses synthetic ScoredCritique fixtures — no API calls needed.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from autocritic.critic import CritiqueResult
from autocritic.scoring import AxisScore, ScoredCritique
from evals.rubrics.usefulness import CritiqueExpectation, EXPECTATIONS
from evals.usefulness import (
    _deserialize_scored_critique,
    _serialize_scored_critique,
    eval_completeness,
    eval_expected_terms,
    eval_lens_vocabulary,
    eval_score_text_coherence,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_expectation(
    critic_id: str = "wolfflin",
    image_name: str = "linear_composition",
    expected_terms: list[str] | None = None,
) -> CritiqueExpectation:
    return CritiqueExpectation(
        critic_id=critic_id,
        image_name=image_name,
        expected_terms=expected_terms or ["linear", "contour", "edge", "bounded"],
    )


_SENTINEL = object()


def _make_scored_critique(
    critic_id: str = "wolfflin",
    raw_text: str = "",
    lens_summary: str = "A linear composition with clear contour edges.",
    strengths: list[str] | object = _SENTINEL,
    weaknesses: list[str] | object = _SENTINEL,
    directives: list[str] | object = _SENTINEL,
    axis_scores: list[AxisScore] | object = _SENTINEL,
) -> ScoredCritique:
    if strengths is _SENTINEL:
        strengths = [
            "Decisive linear commitment with clear contour definition",
            "Strong planar organization parallel to the picture plane",
        ]
    if weaknesses is _SENTINEL:
        weaknesses = [
            "The multiplicity feels mechanical rather than compositionally structured",
            "The recession axis is unexplored — purely frontal presentation",
        ]
    if directives is _SENTINEL:
        directives = [
            "Introduce overlapping forms to activate the plane/recession polarity",
            "Consider softening one edge to create a local painterly moment",
        ]
    critique = CritiqueResult(
        critic_id=critic_id,
        image_path="test.png",
        model="test",
        raw_text=raw_text or (
            "This image is strongly linear with clear contour edges and bounded "
            "forms. The planar organization and closed form containment show a "
            "commitment to tactile silhouette over tonal mass. The multiplicity "
            "of discrete geometric shapes maintains independent identity. "
            "Absolute clarity and painterly dissolution are at opposite poles here."
        ),
        lens_summary=lens_summary,
        strengths=strengths,
        weaknesses=weaknesses,
        directives=directives,
    )
    if axis_scores is _SENTINEL:
        axis_scores = [
            AxisScore("linear_painterly", "Linear vs. Painterly", -0.9, "Strongly linear"),
            AxisScore("plane_recession", "Plane vs. Recession", -0.8, "Strongly planar"),
            AxisScore("closed_open", "Closed vs. Open Form", -0.7, "Closed form"),
            AxisScore("multiplicity_unity", "Multiplicity vs. Unity", -0.5, "Moderate multiplicity"),
            AxisScore("clearness_unclearness", "Clearness vs. Unclearness", -0.85, "Absolute clarity"),
        ]
    return ScoredCritique(critique=critique, axis_scores=axis_scores, composite_score=0.75)


# ---------------------------------------------------------------------------
# Serialization round-trip
# ---------------------------------------------------------------------------

class TestSerialization:
    def test_round_trip(self):
        sc = _make_scored_critique()
        data = _serialize_scored_critique(sc)
        restored = _deserialize_scored_critique(data)
        assert restored.critique.critic_id == sc.critique.critic_id
        assert restored.critique.lens_summary == sc.critique.lens_summary
        assert len(restored.axis_scores) == len(sc.axis_scores)
        assert restored.composite_score == sc.composite_score

    def test_preserves_all_fields(self):
        sc = _make_scored_critique()
        data = _serialize_scored_critique(sc)
        restored = _deserialize_scored_critique(data)
        assert restored.critique.strengths == sc.critique.strengths
        assert restored.critique.weaknesses == sc.critique.weaknesses
        assert restored.critique.directives == sc.critique.directives
        for orig, rest in zip(sc.axis_scores, restored.axis_scores):
            assert rest.axis_id == orig.axis_id
            assert rest.score == orig.score
            assert rest.reasoning == orig.reasoning


# ---------------------------------------------------------------------------
# Completeness
# ---------------------------------------------------------------------------

class TestCompleteness:
    def test_complete_critique_passes(self):
        exp = _make_expectation()
        sc = _make_scored_critique()
        result = eval_completeness(exp, sc)
        assert result.passed

    def test_empty_lens_summary_fails(self):
        exp = _make_expectation()
        sc = _make_scored_critique(lens_summary="")
        result = eval_completeness(exp, sc)
        assert not result.passed

    def test_no_directives_fails(self):
        exp = _make_expectation()
        sc = _make_scored_critique(directives=[])
        result = eval_completeness(exp, sc)
        assert not result.passed

    def test_short_directives_fail(self):
        exp = _make_expectation()
        sc = _make_scored_critique(directives=["Fix it", "More contrast"])
        result = eval_completeness(exp, sc)
        assert not result.passed

    def test_no_strengths_fails(self):
        exp = _make_expectation()
        sc = _make_scored_critique(strengths=[])
        result = eval_completeness(exp, sc)
        assert not result.passed

    def test_no_axis_scores_fails(self):
        exp = _make_expectation()
        sc = _make_scored_critique(axis_scores=[])
        result = eval_completeness(exp, sc)
        assert not result.passed

    def test_empty_reasoning_fails(self):
        exp = _make_expectation()
        scores = [AxisScore("linear_painterly", "Linear", -0.9, "")]
        sc = _make_scored_critique(axis_scores=scores)
        result = eval_completeness(exp, sc)
        assert not result.passed


# ---------------------------------------------------------------------------
# Lens vocabulary
# ---------------------------------------------------------------------------

class TestLensVocabulary:
    def test_distinctive_vocabulary_passes(self):
        exp = _make_expectation()
        sc = _make_scored_critique()
        result = eval_lens_vocabulary(exp, sc)
        assert result.passed

    def test_generic_only_fails(self):
        exp = _make_expectation()
        sc = _make_scored_critique(
            raw_text=(
                "The composition shows good balance and contrast with effective "
                "use of negative space. The visual hierarchy creates a strong "
                "focal point. The rhythm and flow guide the viewer through the "
                "design. Good use of proportion and emphasis throughout."
            ),
        )
        result = eval_lens_vocabulary(exp, sc)
        assert not result.passed

    def test_no_ground_truth_still_returns_result(self):
        # Critic with no ground truth module
        exp = _make_expectation(critic_id="nonexistent")
        sc = _make_scored_critique(critic_id="nonexistent")
        result = eval_lens_vocabulary(exp, sc)
        assert not result.passed  # fails because no ground truth


# ---------------------------------------------------------------------------
# Expected terms
# ---------------------------------------------------------------------------

class TestExpectedTerms:
    def test_all_terms_present_passes(self):
        exp = _make_expectation(expected_terms=["linear", "contour", "edge", "bounded"])
        sc = _make_scored_critique()
        result = eval_expected_terms(exp, sc)
        assert result.passed

    def test_most_terms_present_passes(self):
        # 3/4 = 75%, which meets threshold
        exp = _make_expectation(expected_terms=["linear", "contour", "edge", "zigzag"])
        sc = _make_scored_critique()
        result = eval_expected_terms(exp, sc)
        assert result.passed

    def test_few_terms_present_fails(self):
        # Only 1/4 = 25%, below threshold
        exp = _make_expectation(expected_terms=["zigzag", "spiral", "fractal", "linear"])
        sc = _make_scored_critique()
        result = eval_expected_terms(exp, sc)
        assert not result.passed


# ---------------------------------------------------------------------------
# Score-text coherence
# ---------------------------------------------------------------------------

class TestCoherence:
    def test_low_scores_addressed_passes(self):
        """Bipolar: low-commitment axes (near 0) mentioned in weaknesses."""
        exp = _make_expectation()
        # multiplicity_unity at -0.1 is low commitment for bipolar
        scores = [
            AxisScore("linear_painterly", "Linear vs. Painterly", -0.9, "Strongly linear"),
            AxisScore("multiplicity_unity", "Multiplicity vs. Unity", -0.1, "Ambiguous"),
        ]
        sc = _make_scored_critique(
            axis_scores=scores,
            weaknesses=["The multiplicity/unity axis is unresolved and ambiguous"],
        )
        result = eval_score_text_coherence(exp, sc)
        assert result.passed

    def test_no_low_scores_trivially_passes(self):
        """All scores show strong commitment — no coherence issue."""
        exp = _make_expectation()
        sc = _make_scored_critique()  # default scores are all high commitment
        result = eval_score_text_coherence(exp, sc)
        assert result.passed

    def test_unipolar_low_score_addressed(self):
        """Unipolar: low score (< 0.4) should be mentioned."""
        exp = _make_expectation(critic_id="arnheim")
        scores = [
            AxisScore("balance", "Balance", 0.2, "Severely unbalanced"),
            AxisScore("simplicity", "Simplicity", 0.8, "Clear structure"),
        ]
        sc = _make_scored_critique(
            critic_id="arnheim",
            axis_scores=scores,
            weaknesses=["The balance is severely lacking, with unresolved weight distribution"],
        )
        result = eval_score_text_coherence(exp, sc)
        assert result.passed


# ---------------------------------------------------------------------------
# Rubric data structure
# ---------------------------------------------------------------------------

class TestRubricData:
    def test_all_expectations_have_images(self):
        for exp in EXPECTATIONS:
            assert exp.image_path.exists(), (
                f"{exp.critic_id}/{exp.image_name}: image not found at {exp.image_path}"
            )

    def test_all_expectations_have_terms(self):
        for exp in EXPECTATIONS:
            assert len(exp.expected_terms) >= 3, (
                f"{exp.critic_id}/{exp.image_name}: needs at least 3 expected terms"
            )

    def test_expectations_cover_all_critics(self):
        critics = set(e.critic_id for e in EXPECTATIONS)
        assert critics == {
            "wolfflin", "dow", "kandinsky", "arnheim", "gombrich",
            "albers", "klee", "ruskin", "hildebrand", "worringer",
        }

    def test_each_critic_has_two_images(self):
        from collections import Counter
        counts = Counter(e.critic_id for e in EXPECTATIONS)
        for critic_id, count in counts.items():
            assert count == 2, f"{critic_id} has {count} images, expected 2"
