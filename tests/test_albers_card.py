"""
Evaluate the Albers critic card against ground truth.

Albers' framework is about color interaction — the fact that color
deceives continually and is the most relative medium in art. The most
distinctive feature is the insistence on contextual analysis: what
matters is not what a color IS but what it DOES to its neighbors.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from evals.ground_truth import albers as gt

CARD_PATH = Path(__file__).resolve().parent.parent / "critics" / "albers.json"


@pytest.fixture
def card() -> dict:
    if not CARD_PATH.exists():
        pytest.skip("Albers critic card not yet produced")
    return json.loads(CARD_PATH.read_text())


class TestCoreConceptCoverage:
    """All five core concepts must be present with full operational detail."""

    EXPECTED_CONCEPTS = {
        "color_relativity", "simultaneous_contrast",
        "color_boundaries", "color_quantity", "film_and_volume_color",
    }

    def test_has_all_five_concepts(self, card: dict):
        concept_ids = {c["concept_id"] for c in card["core_concepts"]}
        assert self.EXPECTED_CONCEPTS == concept_ids, (
            f"Missing: {self.EXPECTED_CONCEPTS - concept_ids}, "
            f"Extra: {concept_ids - self.EXPECTED_CONCEPTS}"
        )

    def test_each_concept_has_definition(self, card: dict):
        for c in card["core_concepts"]:
            assert "definition" in c, f"{c['concept_id']} missing definition"
            assert len(c["definition"]) >= 50, (
                f"{c['concept_id']} definition too short"
            )

    def test_each_concept_has_diagnostic_questions(self, card: dict):
        for c in card["core_concepts"]:
            qs = c.get("diagnostic_questions", [])
            assert len(qs) >= 3, (
                f"{c['concept_id']} needs at least 3 diagnostic questions, has {len(qs)}"
            )

    def test_each_concept_has_indicators(self, card: dict):
        for c in card["core_concepts"]:
            indicators = c.get("indicators", {})
            assert len(indicators) >= 2, (
                f"{c['concept_id']} needs at least 2 indicator categories"
            )

    def test_each_concept_has_feedback_directions(self, card: dict):
        for c in card["core_concepts"]:
            fb = c.get("feedback_directions", {})
            assert len(fb) >= 2, (
                f"{c['concept_id']} needs at least 2 feedback direction categories"
            )

    def test_each_concept_has_common_misreadings(self, card: dict):
        for c in card["core_concepts"]:
            misreadings = c.get("common_misreadings", [])
            assert len(misreadings) >= 2, (
                f"{c['concept_id']} needs at least 2 common_misreadings"
            )


class TestColorRelativity:
    """The central claim: color is never seen as it physically is."""

    def test_relativity_mentions_context(self, card: dict):
        cr = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "color_relativity")
        defn = cr["definition"].lower()
        assert "context" in defn or "neighbor" in defn or "ground" in defn, (
            "Relativity definition must mention context-dependence"
        )

    def test_relativity_mentions_physical_vs_psychic(self, card: dict):
        cr = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "color_relativity")
        defn = cr["definition"].lower()
        assert "physical" in defn and ("psychic" in defn or "perceived" in defn or "perception" in defn), (
            "Relativity must mention discrepancy between physical and psychic/perceived"
        )

    def test_mentions_subtraction_principle(self, card: dict):
        text = json.dumps(card).lower()
        assert "subtract" in text, "Card must mention the subtraction principle"

    def test_one_color_appears_as_two(self, card: dict):
        """Core demonstration: same color on different grounds reads differently."""
        cr = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "color_relativity")
        all_text = json.dumps(cr).lower()
        assert "different" in all_text and "ground" in all_text, (
            "Relativity must discuss color changing on different grounds"
        )


class TestSimultaneousContrast:
    """After-image and simultaneous contrast are inescapable."""

    def test_mentions_after_image(self, card: dict):
        sc = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "simultaneous_contrast")
        all_text = json.dumps(sc).lower()
        assert "after-image" in all_text or "afterimage" in all_text, (
            "Must mention after-image"
        )

    def test_mentions_retinal(self, card: dict):
        sc = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "simultaneous_contrast")
        all_text = json.dumps(sc).lower()
        assert "retinal" in all_text or "receptor" in all_text, (
            "Must mention retinal/physiological basis"
        )

    def test_no_eye_is_foolproof(self, card: dict):
        """Albers' strongest claim about color deception."""
        text = json.dumps(card).lower()
        assert "foolproof" in text or "no eye" in text or "no normal eye" in text, (
            "Card must state that no eye is immune to color deception"
        )


class TestColorBoundaries:
    """Boundary types determine spatial reading."""

    def test_mentions_hard_soft_boundaries(self, card: dict):
        cb = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "color_boundaries")
        all_text = json.dumps(cb).lower()
        assert "hard" in all_text and "soft" in all_text, (
            "Must discuss both hard and soft boundaries"
        )

    def test_mentions_vibrating_boundaries(self, card: dict):
        cb = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "color_boundaries")
        all_text = json.dumps(cb).lower()
        assert "vibrat" in all_text, "Must discuss vibrating boundaries"

    def test_mentions_vanishing_boundaries(self, card: dict):
        cb = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "color_boundaries")
        all_text = json.dumps(cb).lower()
        assert "vanish" in all_text, "Must discuss vanishing boundaries"

    def test_boundaries_determine_space(self, card: dict):
        cb = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "color_boundaries")
        defn = cb["definition"].lower()
        assert "spatial" in defn or "space" in defn or "depth" in defn, (
            "Boundaries must be connected to spatial reading"
        )


class TestColorQuantity:
    """Weber-Fechner and color intervals."""

    def test_mentions_weber_fechner(self, card: dict):
        cq = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "color_quantity")
        all_text = json.dumps(cq).lower()
        assert "weber" in all_text or "fechner" in all_text, (
            "Must mention Weber-Fechner Law"
        )

    def test_mentions_intervals(self, card: dict):
        cq = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "color_quantity")
        all_text = json.dumps(cq).lower()
        assert "interval" in all_text, "Must discuss color intervals"

    def test_mentions_bezold(self, card: dict):
        text = json.dumps(card).lower()
        assert "bezold" in text, "Card must mention the Bezold effect"


class TestEssentialClaims:
    """The card must preserve Albers' essential theoretical commitments."""

    def test_has_anti_goals(self, card: dict):
        goals = card.get("anti_goals", [])
        assert len(goals) >= 5, f"Need at least 5 anti-goals, have {len(goals)}"

    def test_anti_goals_reject_isolation(self, card: dict):
        all_anti = " ".join(card.get("anti_goals", [])).lower()
        assert "isolation" in all_anti, (
            "Anti-goals must reject evaluating color in isolation"
        )

    def test_anti_goals_reject_harmony_systems(self, card: dict):
        all_anti = " ".join(card.get("anti_goals", [])).lower()
        assert "harmony" in all_anti or "color wheel" in all_anti, (
            "Anti-goals must reject color wheel/harmony systems as starting points"
        )

    def test_has_tensions(self, card: dict):
        tensions = card.get("tensions", [])
        assert len(tensions) >= 2, f"Need at least 2 tensions, have {len(tensions)}"

    def test_has_citations(self, card: dict):
        citations = card.get("citations", [])
        assert len(citations) >= 5, f"Need at least 5 citations, have {len(citations)}"

    def test_has_confidence_notes(self, card: dict):
        notes = card.get("confidence_notes", [])
        assert len(notes) >= 2, f"Need at least 2 confidence notes, have {len(notes)}"

    def test_thesis_mentions_relativity(self, card: dict):
        thesis = card.get("thesis", "").lower()
        assert "relative" in thesis or "relativity" in thesis, (
            "Thesis must mention color relativity"
        )

    def test_thesis_mentions_interaction(self, card: dict):
        thesis = card.get("thesis", "").lower()
        assert "interaction" in thesis, "Thesis must mention interaction"

    def test_dissonance_as_desirable(self, card: dict):
        """Albers refuses to privilege harmony over dissonance."""
        text = json.dumps(card).lower()
        assert "dissonance" in text, "Card must mention dissonance as desirable"


class TestDistinctiveVocabulary:
    """The card must use Albers' actual terms, not generic color language."""

    def test_uses_distinctive_terms(self, card: dict):
        text = json.dumps(card).lower()
        vocab = [v.lower() for v in gt.DISTINCTIVE_VOCABULARY]
        hits = [v for v in vocab if v in text]
        ratio = len(hits) / len(vocab)
        assert ratio >= 0.5, (
            f"Only {len(hits)}/{len(vocab)} ({ratio:.0%}) distinctive terms found. "
            f"Missing: {set(vocab) - set(hits)}"
        )

    def test_uses_key_albers_terms(self, card: dict):
        """These specific terms are non-negotiable for an Albers card."""
        text = json.dumps(card).lower()
        must_have = ["interaction", "simultaneous contrast", "subtraction",
                     "vanishing boundaries", "film color", "weber-fechner"]
        missing = [t for t in must_have if t not in text]
        assert not missing, f"Missing essential Albers terms: {missing}"

    def test_generic_vocabulary_does_not_dominate(self, card: dict):
        from evals.fixtures.generic_baseline import GENERIC_VOCABULARY
        text = json.dumps(card).lower()
        distinctive_hits = sum(1 for v in gt.DISTINCTIVE_VOCABULARY if v.lower() in text)
        generic_hits = sum(1 for v in GENERIC_VOCABULARY if v.lower() in text)
        assert distinctive_hits >= generic_hits, (
            f"Generic vocabulary ({generic_hits}) outnumbers distinctive ({distinctive_hits})"
        )
