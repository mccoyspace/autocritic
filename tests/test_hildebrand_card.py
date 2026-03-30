"""
Evaluate the Hildebrand critic card against ground truth.

Hildebrand's framework is about spatial unity — the conception of relief as
the single unifying principle. The most distinctive features are: the
actual/perceptual form distinction, the hierarchy of spatial over functional
values, the visual projection (Fernbild) as the fundamental mode of artistic
perception, and the architectonic method as the path from imitation to art.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from evals.ground_truth import hildebrand as gt

CARD_PATH = Path(__file__).resolve().parent.parent / "critics" / "hildebrand.json"


@pytest.fixture
def card() -> dict:
    if not CARD_PATH.exists():
        pytest.skip("Hildebrand critic card not yet produced")
    return json.loads(CARD_PATH.read_text())


class TestCoreConceptCoverage:
    """All five core concepts must be present with full operational detail."""

    EXPECTED_CONCEPTS = {
        "actual_vs_perceptual_form", "conception_of_relief",
        "spatial_vs_functional_values", "visual_projection",
        "architectonic_method",
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


class TestActualVsPerceptualForm:
    """The central dichotomy: form as measured vs. form as seen."""

    def test_mentions_actual_form(self, card: dict):
        af = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "actual_vs_perceptual_form")
        defn = af["definition"].lower()
        assert "actual" in defn, "Must mention actual form"

    def test_mentions_perceptual_form(self, card: dict):
        af = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "actual_vs_perceptual_form")
        defn = af["definition"].lower()
        assert "perceptual" in defn, "Must mention perceptual form"

    def test_art_operates_in_perceptual(self, card: dict):
        af = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "actual_vs_perceptual_form")
        all_text = json.dumps(af).lower()
        assert "art" in all_text and "perceptual" in all_text, (
            "Must state that art operates in the domain of perceptual form"
        )

    def test_relational_values(self, card: dict):
        """All values are relative — meaning only in relation to all others."""
        text = json.dumps(card).lower()
        assert "relative" in text or "relational" in text, (
            "Card must mention that all values are relative"
        )


class TestConceptionOfRelief:
    """The master principle: all form resolves into a relief reading."""

    def test_mentions_relief(self, card: dict):
        cr = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "conception_of_relief")
        defn = cr["definition"].lower()
        assert "relief" in defn, "Must mention relief"

    def test_mentions_front_and_back_planes(self, card: dict):
        cr = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "conception_of_relief")
        all_text = json.dumps(cr).lower()
        assert "front" in all_text and "back" in all_text, (
            "Must mention front and back planes"
        )

    def test_mentions_plane_unity(self, card: dict):
        cr = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "conception_of_relief")
        all_text = json.dumps(cr).lower()
        assert "plane" in all_text and "unity" in all_text, (
            "Must mention plane unity"
        )

    def test_applies_to_all_art(self, card: dict):
        """Relief conception is not literal bas-relief — it applies universally."""
        cr = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "conception_of_relief")
        all_text = json.dumps(cr).lower()
        assert "painting" in all_text or "all" in all_text or "universal" in all_text, (
            "Must indicate relief applies beyond sculpture"
        )

    def test_depth_movement(self, card: dict):
        cr = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "conception_of_relief")
        all_text = json.dumps(cr).lower()
        assert "depth" in all_text, "Must mention depth movement"


class TestSpatialVsFunctionalValues:
    """Spatial values are primary; functional values presuppose them."""

    def test_mentions_spatial_values(self, card: dict):
        sf = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "spatial_vs_functional_values")
        defn = sf["definition"].lower()
        assert "spatial" in defn, "Must mention spatial values"

    def test_mentions_functional_values(self, card: dict):
        sf = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "spatial_vs_functional_values")
        defn = sf["definition"].lower()
        assert "functional" in defn, "Must mention functional values"

    def test_hierarchy(self, card: dict):
        """Spatial values must be identified as primary."""
        sf = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "spatial_vs_functional_values")
        all_text = json.dumps(sf).lower()
        assert "primary" in all_text or "presuppose" in all_text or "precede" in all_text, (
            "Must establish spatial as primary over functional"
        )

    def test_formless_without_spatial(self, card: dict):
        """Functional truth without spatial unity = formless."""
        sf = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "spatial_vs_functional_values")
        all_text = json.dumps(sf).lower()
        assert "formless" in all_text or "without" in all_text, (
            "Must warn that functional without spatial is formless"
        )


class TestVisualProjection:
    """The Fernbild — the unified distance picture."""

    def test_mentions_distance(self, card: dict):
        vp = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "visual_projection")
        all_text = json.dumps(vp).lower()
        assert "distance" in all_text, "Must mention distance viewing"

    def test_mentions_unified(self, card: dict):
        vp = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "visual_projection")
        all_text = json.dumps(vp).lower()
        assert "unified" in all_text or "unity" in all_text or "at a glance" in all_text, (
            "Must mention unified perception / at a glance"
        )

    def test_mentions_two_dimensional(self, card: dict):
        vp = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "visual_projection")
        all_text = json.dumps(vp).lower()
        assert "two-dimensional" in all_text or "plane" in all_text, (
            "Must mention two-dimensional / plane character"
        )

    def test_pure_vision_vs_kinesthetic(self, card: dict):
        """The distinction between pure vision and kinesthetic perception."""
        text = json.dumps(card).lower()
        assert "kinesthetic" in text or "pure vision" in text, (
            "Card must mention the pure vision / kinesthetic distinction"
        )


class TestArchitectonicMethod:
    """The path from imitation to art."""

    def test_mentions_architectonic(self, card: dict):
        am = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "architectonic_method")
        defn = am["definition"].lower()
        assert "architectonic" in defn, "Must mention architectonic"

    def test_opposes_mere_imitation(self, card: dict):
        am = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "architectonic_method")
        all_text = json.dumps(am).lower()
        assert "imitat" in all_text or "naturalism" in all_text, (
            "Must oppose mere imitation/naturalism"
        )

    def test_mentions_spatial_organization(self, card: dict):
        am = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "architectonic_method")
        all_text = json.dumps(am).lower()
        assert "spatial" in all_text or "structure" in all_text or "organization" in all_text, (
            "Must mention spatial organization/structure"
        )


class TestEssentialClaims:
    """The card must preserve Hildebrand's essential theoretical commitments."""

    def test_has_anti_goals(self, card: dict):
        goals = card.get("anti_goals", [])
        assert len(goals) >= 5, f"Need at least 5 anti-goals, have {len(goals)}"

    def test_anti_goals_reject_imitation(self, card: dict):
        all_anti = " ".join(card.get("anti_goals", [])).lower()
        assert "imitat" in all_anti or "photographic" in all_anti, (
            "Anti-goals must reject mere imitation"
        )

    def test_anti_goals_reject_fixed_proportions(self, card: dict):
        all_anti = " ".join(card.get("anti_goals", [])).lower()
        assert "proportion" in all_anti, (
            "Anti-goals must reject fixed proportional systems"
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

    def test_thesis_mentions_spatial_unity(self, card: dict):
        thesis = card.get("thesis", "").lower()
        assert "spatial" in thesis or "unity" in thesis, (
            "Thesis must mention spatial unity"
        )

    def test_thesis_mentions_relief(self, card: dict):
        thesis = card.get("thesis", "").lower()
        assert "relief" in thesis, "Thesis must mention the conception of relief"

    def test_michelangelo_water_metaphor(self, card: dict):
        """Michelangelo's water metaphor for stone carving."""
        text = json.dumps(card).lower()
        assert "water" in text, (
            "Card must include Michelangelo's water/submersion metaphor"
        )


class TestDistinctiveVocabulary:
    """The card must use Hildebrand's actual terms, not generic art language."""

    def test_uses_distinctive_terms(self, card: dict):
        text = json.dumps(card).lower()
        vocab = [v.lower() for v in gt.DISTINCTIVE_VOCABULARY]
        hits = [v for v in vocab if v in text]
        ratio = len(hits) / len(vocab)
        assert ratio >= 0.5, (
            f"Only {len(hits)}/{len(vocab)} ({ratio:.0%}) distinctive terms found. "
            f"Missing: {set(vocab) - set(hits)}"
        )

    def test_uses_key_hildebrand_terms(self, card: dict):
        """These specific terms are non-negotiable for a Hildebrand card."""
        text = json.dumps(card).lower()
        must_have = ["actual form", "perceptual form", "relief",
                     "spatial values", "architectonic", "plane"]
        missing = [t for t in must_have if t not in text]
        assert not missing, f"Missing essential Hildebrand terms: {missing}"

    def test_generic_vocabulary_does_not_dominate(self, card: dict):
        from evals.fixtures.generic_baseline import GENERIC_VOCABULARY
        text = json.dumps(card).lower()
        distinctive_hits = sum(1 for v in gt.DISTINCTIVE_VOCABULARY if v.lower() in text)
        generic_hits = sum(1 for v in GENERIC_VOCABULARY if v.lower() in text)
        assert distinctive_hits >= generic_hits, (
            f"Generic vocabulary ({generic_hits}) outnumbers distinctive ({distinctive_hits})"
        )
