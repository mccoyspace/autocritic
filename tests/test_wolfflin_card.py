"""
Evaluate the Wölfflin critic card against ground truth.

These are the first real distillation evals — testing whether the actual
critic card we produced is faithful to the theory.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from evals.ground_truth import wolfflin as gt

CARD_PATH = Path(__file__).resolve().parent.parent / "critics" / "wolfflin.json"


@pytest.fixture
def card() -> dict:
    if not CARD_PATH.exists():
        pytest.skip("Wölfflin critic card not yet produced")
    return json.loads(CARD_PATH.read_text())


class TestPolarityCoverage:
    """All five polarities must be present as criteria."""

    EXPECTED_POLARITIES = set(gt.POLARITIES.keys())

    def test_has_all_five_polarities(self, card: dict):
        card_ids = {c["criterion_id"] for c in card["criteria"]}
        assert self.EXPECTED_POLARITIES == card_ids, (
            f"Missing: {self.EXPECTED_POLARITIES - card_ids}, "
            f"Extra: {card_ids - self.EXPECTED_POLARITIES}"
        )

    def test_each_polarity_has_two_poles(self, card: dict):
        for crit in card["criteria"]:
            assert "pole_a" in crit, f"{crit['criterion_id']} missing pole_a"
            assert "pole_b" in crit, f"{crit['criterion_id']} missing pole_b"

    def test_each_polarity_has_diagnostic_questions(self, card: dict):
        for crit in card["criteria"]:
            qs = crit.get("diagnostic_questions", [])
            assert len(qs) >= 2, (
                f"{crit['criterion_id']} needs at least 2 diagnostic questions, has {len(qs)}"
            )

    def test_each_polarity_has_indicators_for_both_poles(self, card: dict):
        for crit in card["criteria"]:
            indicators = crit.get("indicators", {})
            for pole in ["pole_a", "pole_b"]:
                items = indicators.get(pole, [])
                assert len(items) >= 3, (
                    f"{crit['criterion_id']}.indicators.{pole} needs at least 3 items, has {len(items)}"
                )

    def test_each_polarity_has_feedback_directions_for_both_poles(self, card: dict):
        for crit in card["criteria"]:
            fb = crit.get("feedback_directions", {})
            for direction in ["toward_a", "toward_b"]:
                items = fb.get(direction, [])
                assert len(items) >= 2, (
                    f"{crit['criterion_id']}.feedback_directions.{direction} needs at least 2 items"
                )


class TestEssentialClaims:
    """The card must preserve Wölfflin's essential theoretical commitments."""

    def test_non_normative_language(self, card: dict):
        """The card must not rank one pole above the other."""
        anti_goals = " ".join(card.get("anti_goals", [])).lower()
        thesis = card.get("thesis", "").lower()
        # Should mention non-ranking somewhere
        assert any(phrase in anti_goals + thesis for phrase in [
            "not rank", "neither pole is superior", "not superior",
            "two conceptions", "different solution", "not a higher stage",
        ]), "Card must explicitly state that neither pole is superior"

    def test_independence_of_axes(self, card: dict):
        """The card must note that the five axes are independent."""
        all_text = json.dumps(card).lower()
        assert "independent" in all_text, "Card must mention independence of the axes"

    def test_has_anti_goals(self, card: dict):
        goals = card.get("anti_goals", [])
        assert len(goals) >= 5, f"Need at least 5 anti-goals, have {len(goals)}"

    def test_has_tensions(self, card: dict):
        tensions = card.get("tensions", [])
        assert len(tensions) >= 2, f"Need at least 2 tensions, have {len(tensions)}"

    def test_has_citations(self, card: dict):
        citations = card.get("citations", [])
        assert len(citations) >= 5, f"Need at least 5 citations, have {len(citations)}"


class TestDistinctiveVocabulary:
    """The card must use Wölfflin's actual terms, not generic art-school language."""

    def test_uses_distinctive_terms(self, card: dict):
        text = json.dumps(card).lower()
        vocab = [v.lower() for v in gt.DISTINCTIVE_VOCABULARY]
        hits = [v for v in vocab if v in text]
        ratio = len(hits) / len(vocab)
        assert ratio >= 0.5, (
            f"Only {len(hits)}/{len(vocab)} ({ratio:.0%}) distinctive terms found. "
            f"Missing: {set(vocab) - set(hits)}"
        )

    def test_uses_key_wolfflin_terms(self, card: dict):
        """These specific terms are non-negotiable for a Wölfflin card."""
        text = json.dumps(card).lower()
        must_have = ["linear", "painterly", "tactile", "contour", "recession", "tectonic"]
        missing = [t for t in must_have if t not in text]
        assert not missing, f"Missing essential Wölfflin terms: {missing}"

    def test_generic_vocabulary_does_not_dominate(self, card: dict):
        from evals.fixtures.generic_baseline import GENERIC_VOCABULARY
        text = json.dumps(card).lower()
        distinctive_hits = sum(1 for v in gt.DISTINCTIVE_VOCABULARY if v.lower() in text)
        generic_hits = sum(1 for v in GENERIC_VOCABULARY if v.lower() in text)
        assert distinctive_hits >= generic_hits, (
            f"Generic vocabulary ({generic_hits}) outnumbers distinctive ({distinctive_hits})"
        )


class TestCommonMisreadings:
    """Each criterion should warn against known misapplications."""

    def test_each_criterion_has_misreadings(self, card: dict):
        for crit in card["criteria"]:
            misreadings = crit.get("common_misreadings", [])
            assert len(misreadings) >= 2, (
                f"{crit['criterion_id']} needs at least 2 common_misreadings"
            )
