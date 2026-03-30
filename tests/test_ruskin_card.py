"""
Evaluate the Ruskin critic card against ground truth.

Ruskin's framework is about perception — the innocence of the eye, seeing
flat stains of colour rather than what we know things to be. The most
distinctive features are: the innocence of the eye as foundational principle,
gradation as supreme technical value, the nine laws of composition (especially
principality, curvature, interchange), mystery as a law of nature, and the
insistence that all great art is delicate.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from evals.ground_truth import ruskin as gt

CARD_PATH = Path(__file__).resolve().parent.parent / "critics" / "ruskin.json"


@pytest.fixture
def card() -> dict:
    if not CARD_PATH.exists():
        pytest.skip("Ruskin critic card not yet produced")
    return json.loads(CARD_PATH.read_text())


class TestCoreConceptCoverage:
    """All five core concepts must be present with full operational detail."""

    EXPECTED_CONCEPTS = {
        "innocence_of_the_eye", "gradation",
        "laws_of_composition", "mystery_and_partial_seeing",
        "delicacy_and_patience",
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


class TestInnocenceOfTheEye:
    """The foundational principle: perception before execution."""

    def test_mentions_childish_perception(self, card: dict):
        ie = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "innocence_of_the_eye")
        defn = ie["definition"].lower()
        assert "childish" in defn or "infantine" in defn, (
            "Must mention childish/infantine perception"
        )

    def test_mentions_flat_stains(self, card: dict):
        ie = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "innocence_of_the_eye")
        all_text = json.dumps(ie).lower()
        assert "flat stain" in all_text or "flat patch" in all_text, (
            "Must mention flat stains/patches of colour"
        )

    def test_mentions_blind_man(self, card: dict):
        ie = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "innocence_of_the_eye")
        all_text = json.dumps(ie).lower()
        assert "blind" in all_text, "Must mention the blind man analogy"

    def test_perception_before_technique(self, card: dict):
        ie = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "innocence_of_the_eye")
        all_text = json.dumps(ie).lower()
        assert "perception" in all_text or "seeing" in all_text, (
            "Must frame innocence as a perceptual principle"
        )


class TestGradation:
    """Gradation is the supreme technical value — roundness is the problem."""

    def test_mentions_roundness(self, card: dict):
        gr = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "gradation")
        defn = gr["definition"].lower()
        assert "roundness" in defn or "round" in defn, (
            "Must mention roundness as the fundamental problem"
        )

    def test_mentions_continuous_transition(self, card: dict):
        gr = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "gradation")
        defn = gr["definition"].lower()
        assert "transition" in defn or "continuous" in defn or "gradual" in defn, (
            "Must describe gradation as continuous transition"
        )

    def test_mentions_curved_surfaces(self, card: dict):
        gr = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "gradation")
        all_text = json.dumps(gr).lower()
        assert "curved" in all_text or "curve" in all_text, (
            "Must mention curved surfaces"
        )

    def test_local_colour_inseparable(self, card: dict):
        """Light/shade must not be separated from local colour."""
        text = json.dumps(card).lower()
        assert "local colour" in text or "local color" in text, (
            "Card must mention local colour as inseparable from light"
        )


class TestLawsOfComposition:
    """The nine laws — especially principality, curvature, interchange."""

    def test_mentions_principality(self, card: dict):
        lc = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "laws_of_composition")
        all_text = json.dumps(lc).lower()
        assert "principality" in all_text, "Must mention principality"

    def test_mentions_curvature(self, card: dict):
        lc = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "laws_of_composition")
        all_text = json.dumps(lc).lower()
        assert "curvature" in all_text, "Must mention curvature"

    def test_mentions_interchange(self, card: dict):
        lc = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "laws_of_composition")
        all_text = json.dumps(lc).lower()
        assert "interchange" in all_text, "Must mention interchange"

    def test_mentions_radiation(self, card: dict):
        lc = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "laws_of_composition")
        all_text = json.dumps(lc).lower()
        assert "radiation" in all_text, "Must mention radiation"

    def test_composition_concealed(self, card: dict):
        """Great composition conceals its artifice."""
        lc = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "laws_of_composition")
        all_text = json.dumps(lc).lower()
        assert "conceal" in all_text or "vulgar" in all_text, (
            "Must warn that obvious composition is vulgar"
        )

    def test_mentions_repetition(self, card: dict):
        lc = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "laws_of_composition")
        all_text = json.dumps(lc).lower()
        assert "repetition" in all_text, "Must mention repetition"


class TestMystery:
    """Nothing is ever seen perfectly — mystery is a law of nature."""

    def test_mentions_fragments(self, card: dict):
        ms = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "mystery_and_partial_seeing")
        all_text = json.dumps(ms).lower()
        assert "fragment" in all_text or "partial" in all_text, (
            "Must mention fragmentary/partial seeing"
        )

    def test_mentions_obscurity(self, card: dict):
        ms = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "mystery_and_partial_seeing")
        all_text = json.dumps(ms).lower()
        assert "obscur" in all_text or "incomplet" in all_text, (
            "Must mention obscurity or incompleteness"
        )

    def test_mystery_is_positive(self, card: dict):
        """Mystery is not a defect — it is a law of nature."""
        ms = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "mystery_and_partial_seeing")
        all_text = json.dumps(ms).lower()
        assert "law" in all_text or "truth" in all_text or "nature" in all_text, (
            "Mystery must be framed as a natural law, not a defect"
        )


class TestDelicacyAndPatience:
    """All great art is delicate — anti-bravura is Ruskin's strongest claim."""

    def test_mentions_delicate(self, card: dict):
        dp = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "delicacy_and_patience")
        defn = dp["definition"].lower()
        assert "delica" in defn, "Must mention delicacy"

    def test_mentions_refinement_of_perception(self, card: dict):
        dp = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "delicacy_and_patience")
        all_text = json.dumps(dp).lower()
        assert "refinement" in all_text or "perception" in all_text, (
            "Must mention refinement of perception"
        )

    def test_opposes_boldness(self, card: dict):
        dp = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "delicacy_and_patience")
        all_text = json.dumps(dp).lower()
        assert "bold" in all_text or "dash" in all_text or "bravura" in all_text, (
            "Must oppose boldness/dash/bravura"
        )

    def test_nature_not_bold(self, card: dict):
        """Nature is never bold — Ruskin's argument from natural law."""
        text = json.dumps(card).lower()
        assert "nature" in text and "bold" in text, (
            "Card must connect nature's lack of boldness to the anti-bravura principle"
        )


class TestEssentialClaims:
    """The card must preserve Ruskin's essential theoretical commitments."""

    def test_has_anti_goals(self, card: dict):
        goals = card.get("anti_goals", [])
        assert len(goals) >= 5, f"Need at least 5 anti-goals, have {len(goals)}"

    def test_anti_goals_reject_boldness(self, card: dict):
        all_anti = " ".join(card.get("anti_goals", [])).lower()
        assert "bold" in all_anti or "bravura" in all_anti or "dash" in all_anti, (
            "Anti-goals must reject boldness/bravura/dash"
        )

    def test_anti_goals_reject_outline(self, card: dict):
        all_anti = " ".join(card.get("anti_goals", [])).lower()
        assert "outline" in all_anti, (
            "Anti-goals must reject drawing by outline"
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

    def test_thesis_mentions_perception(self, card: dict):
        thesis = card.get("thesis", "").lower()
        assert "perception" in thesis or "innocence" in thesis or "seeing" in thesis, (
            "Thesis must mention perception or innocence of the eye"
        )

    def test_thesis_mentions_delicacy(self, card: dict):
        thesis = card.get("thesis", "").lower()
        assert "delica" in thesis, (
            "Thesis must mention delicacy"
        )

    def test_colour_relative_form_absolute(self, card: dict):
        """Ruskin's distinctive epistemological claim."""
        text = json.dumps(card).lower()
        assert "relative" in text and "absolute" in text, (
            "Card must state that colour is relative and form is absolute"
        )


class TestDistinctiveVocabulary:
    """The card must use Ruskin's actual terms, not generic art language."""

    def test_uses_distinctive_terms(self, card: dict):
        text = json.dumps(card).lower()
        vocab = [v.lower() for v in gt.DISTINCTIVE_VOCABULARY]
        hits = [v for v in vocab if v in text]
        ratio = len(hits) / len(vocab)
        assert ratio >= 0.5, (
            f"Only {len(hits)}/{len(vocab)} ({ratio:.0%}) distinctive terms found. "
            f"Missing: {set(vocab) - set(hits)}"
        )

    def test_uses_key_ruskin_terms(self, card: dict):
        """These specific terms are non-negotiable for a Ruskin card."""
        text = json.dumps(card).lower()
        must_have = ["innocence of the eye", "gradation", "principality",
                     "mystery", "delicacy", "roundness"]
        missing = [t for t in must_have if t not in text]
        assert not missing, f"Missing essential Ruskin terms: {missing}"

    def test_generic_vocabulary_does_not_dominate(self, card: dict):
        from evals.fixtures.generic_baseline import GENERIC_VOCABULARY
        text = json.dumps(card).lower()
        distinctive_hits = sum(1 for v in gt.DISTINCTIVE_VOCABULARY if v.lower() in text)
        generic_hits = sum(1 for v in GENERIC_VOCABULARY if v.lower() in text)
        assert distinctive_hits >= generic_hits, (
            f"Generic vocabulary ({generic_hits}) outnumbers distinctive ({distinctive_hits})"
        )
