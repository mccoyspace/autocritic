"""
Evaluate the Klee critic card against ground truth.

Klee's framework is about genesis — forms as records of movement and
energy. The most distinctive features are: the three conjugations
(active, medial, passive), non-symmetrical balance through counterweights,
and the arrow as the metaphor for directed aspiration.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from evals.ground_truth import klee as gt

CARD_PATH = Path(__file__).resolve().parent.parent / "critics" / "klee.json"


@pytest.fixture
def card() -> dict:
    if not CARD_PATH.exists():
        pytest.skip("Klee critic card not yet produced")
    return json.loads(CARD_PATH.read_text())


class TestCoreConceptCoverage:
    """All five core concepts must be present with full operational detail."""

    EXPECTED_CONCEPTS = {
        "line_as_movement", "structural_rhythm",
        "non_symmetrical_balance", "gravitational_dynamics",
        "kinetic_chromatic_energy",
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


class TestThreeConjugations:
    """The active/medial/passive grammar is Klee's most distinctive feature."""

    def test_mentions_active_line(self, card: dict):
        lm = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "line_as_movement")
        defn = lm["definition"].lower()
        assert "active" in defn, "Must mention active line"

    def test_mentions_medial_line(self, card: dict):
        lm = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "line_as_movement")
        all_text = json.dumps(lm).lower()
        assert "medial" in all_text, "Must mention medial line"

    def test_mentions_passive_line(self, card: dict):
        lm = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "line_as_movement")
        all_text = json.dumps(lm).lower()
        assert "passive" in all_text, "Must mention passive line"

    def test_mentions_conjugation(self, card: dict):
        text = json.dumps(card).lower()
        assert "conjugat" in text, "Card must mention conjugations"

    def test_line_as_walk(self, card: dict):
        """Klee's iconic formulation."""
        lm = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "line_as_movement")
        defn = lm["definition"].lower()
        assert "walk" in defn, "Must mention line on a walk"

    def test_line_as_point_in_motion(self, card: dict):
        lm = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "line_as_movement")
        defn = lm["definition"].lower()
        assert "point" in defn and "motion" in defn or "shifting" in defn, (
            "Must describe line as a point in motion"
        )


class TestNonSymmetricalBalance:
    """Balance through counterweights, not mirror symmetry."""

    def test_mentions_counterweight(self, card: dict):
        nsb = next(c for c in card["core_concepts"]
                   if c["concept_id"] == "non_symmetrical_balance")
        all_text = json.dumps(nsb).lower()
        assert "counterweight" in all_text, "Must mention counterweights"

    def test_mentions_tightrope_walker(self, card: dict):
        nsb = next(c for c in card["core_concepts"]
                   if c["concept_id"] == "non_symmetrical_balance")
        all_text = json.dumps(nsb).lower()
        assert "tightrope" in all_text, "Must mention the tightrope walker"

    def test_mentions_tower_building(self, card: dict):
        nsb = next(c for c in card["core_concepts"]
                   if c["concept_id"] == "non_symmetrical_balance")
        all_text = json.dumps(nsb).lower()
        assert "tower" in all_text, "Must mention tower-building principle"

    def test_balance_not_symmetry(self, card: dict):
        nsb = next(c for c in card["core_concepts"]
                   if c["concept_id"] == "non_symmetrical_balance")
        defn = nsb["definition"].lower()
        assert "not" in defn and "symmetry" in defn, (
            "Must distinguish balance from symmetry"
        )


class TestGravitationalDynamics:
    """The arrow and the tension between constraint and aspiration."""

    def test_mentions_arrow(self, card: dict):
        gd = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "gravitational_dynamics")
        all_text = json.dumps(gd).lower()
        assert "arrow" in all_text, "Must mention the arrow"

    def test_mentions_gravity(self, card: dict):
        gd = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "gravitational_dynamics")
        defn = gd["definition"].lower()
        assert "gravity" in defn or "gravit" in defn, (
            "Must mention gravity"
        )

    def test_half_winged_half_imprisoned(self, card: dict):
        """Klee's most famous aphorism from this text."""
        text = json.dumps(card).lower()
        assert "half winged" in text or "half imprisoned" in text, (
            "Card must include 'half winged, half imprisoned'"
        )

    def test_mentions_transitional_regions(self, card: dict):
        gd = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "gravitational_dynamics")
        all_text = json.dumps(gd).lower()
        assert "water" in all_text or "atmosphere" in all_text or "transitional" in all_text, (
            "Must mention transitional regions (water, atmosphere)"
        )


class TestKineticEnergy:
    """Pendulum, spinning top, spiral — the kinetic vocabulary."""

    def test_mentions_pendulum(self, card: dict):
        ke = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "kinetic_chromatic_energy")
        all_text = json.dumps(ke).lower()
        assert "pendulum" in all_text, "Must mention the pendulum"

    def test_mentions_spinning_top(self, card: dict):
        ke = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "kinetic_chromatic_energy")
        all_text = json.dumps(ke).lower()
        assert "spinning" in all_text, "Must mention the spinning top"

    def test_mentions_spiral(self, card: dict):
        ke = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "kinetic_chromatic_energy")
        all_text = json.dumps(ke).lower()
        assert "spiral" in all_text, "Must mention the spiral"

    def test_mentions_chromatic_energy(self, card: dict):
        ke = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "kinetic_chromatic_energy")
        all_text = json.dumps(ke).lower()
        assert "chromatic" in all_text, "Must mention chromatic energy"


class TestStructuralRhythm:
    """Structural vs. individual articulation."""

    def test_mentions_repetitive(self, card: dict):
        sr = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "structural_rhythm")
        defn = sr["definition"].lower()
        assert "repetit" in defn, "Must mention repetition as structural"

    def test_mentions_golden_section(self, card: dict):
        sr = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "structural_rhythm")
        all_text = json.dumps(sr).lower()
        assert "golden section" in all_text, "Must mention Golden Section"

    def test_mentions_individual_articulation(self, card: dict):
        sr = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "structural_rhythm")
        all_text = json.dumps(sr).lower()
        assert "individual" in all_text, "Must mention individual articulation"


class TestEssentialClaims:
    """The card must preserve Klee's essential theoretical commitments."""

    def test_has_anti_goals(self, card: dict):
        goals = card.get("anti_goals", [])
        assert len(goals) >= 5, f"Need at least 5 anti-goals, have {len(goals)}"

    def test_anti_goals_reject_static_shapes(self, card: dict):
        all_anti = " ".join(card.get("anti_goals", [])).lower()
        assert "static" in all_anti, (
            "Anti-goals must reject treating forms as static shapes"
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

    def test_thesis_mentions_genesis(self, card: dict):
        thesis = card.get("thesis", "").lower()
        assert "genesis" in thesis or "movement" in thesis, (
            "Thesis must mention genesis or movement"
        )


class TestDistinctiveVocabulary:
    """The card must use Klee's actual terms, not generic art language."""

    def test_uses_distinctive_terms(self, card: dict):
        text = json.dumps(card).lower()
        vocab = [v.lower() for v in gt.DISTINCTIVE_VOCABULARY]
        hits = [v for v in vocab if v in text]
        ratio = len(hits) / len(vocab)
        assert ratio >= 0.5, (
            f"Only {len(hits)}/{len(vocab)} ({ratio:.0%}) distinctive terms found. "
            f"Missing: {set(vocab) - set(hits)}"
        )

    def test_uses_key_klee_terms(self, card: dict):
        """These specific terms are non-negotiable for a Klee card."""
        text = json.dumps(card).lower()
        must_have = ["active line", "conjugation", "tightrope",
                     "arrow", "pendulum", "spiral"]
        missing = [t for t in must_have if t not in text]
        assert not missing, f"Missing essential Klee terms: {missing}"

    def test_generic_vocabulary_does_not_dominate(self, card: dict):
        from evals.fixtures.generic_baseline import GENERIC_VOCABULARY
        text = json.dumps(card).lower()
        distinctive_hits = sum(1 for v in gt.DISTINCTIVE_VOCABULARY if v.lower() in text)
        generic_hits = sum(1 for v in GENERIC_VOCABULARY if v.lower() in text)
        assert distinctive_hits >= generic_hits, (
            f"Generic vocabulary ({generic_hits}) outnumbers distinctive ({distinctive_hits})"
        )
