"""
Evaluate the Gombrich critic card against ground truth.

Gombrich's framework is specifically about decorative art and the
psychology of pattern. The most distinctive feature is the information-
theory vocabulary: redundancy vs. information, monotony vs. variety,
and the sense of order as an active monitoring system.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from evals.ground_truth import gombrich as gt

CARD_PATH = Path(__file__).resolve().parent.parent / "critics" / "gombrich.json"


@pytest.fixture
def card() -> dict:
    if not CARD_PATH.exists():
        pytest.skip("Gombrich critic card not yet produced")
    return json.loads(CARD_PATH.read_text())


class TestCoreConceptCoverage:
    """All five core concepts must be present with full operational detail."""

    EXPECTED_CONCEPTS = {
        "sense_of_order", "redundancy_and_information",
        "monotony_and_variety", "grading_of_complexity", "frame_and_fill",
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
            for cat, items in indicators.items():
                assert len(items) >= 2, (
                    f"{c['concept_id']}.indicators.{cat} needs >= 2 items"
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

    def test_each_concept_has_key_concepts(self, card: dict):
        for c in card["core_concepts"]:
            concepts = c.get("key_concepts", [])
            assert len(concepts) >= 3, (
                f"{c['concept_id']} needs at least 3 key_concepts, has {len(concepts)}"
            )


class TestInformationTheoryVocabulary:
    """The card must use Gombrich's information-theory vocabulary —
    this is what distinguishes his framework from generic pattern talk."""

    def test_redundancy_concept_mentions_predictability(self, card: dict):
        ri = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "redundancy_and_information")
        defn = ri["definition"].lower()
        assert "predict" in defn, (
            "Redundancy definition must mention predictability"
        )

    def test_redundancy_concept_mentions_information_theory(self, card: dict):
        ri = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "redundancy_and_information")
        defn = ri["definition"].lower()
        assert "information theory" in defn or "information" in defn, (
            "Redundancy definition must connect to information theory"
        )

    def test_mentions_etc_principle(self, card: dict):
        text = json.dumps(card).lower()
        assert "etc" in text, "Card must mention the 'etc. principle'"

    def test_mentions_habituation(self, card: dict):
        text = json.dumps(card).lower()
        assert "habituat" in text, "Card must discuss habituation"

    def test_mentions_break_detection(self, card: dict):
        text = json.dumps(card).lower()
        assert "break" in text, "Card must discuss breaks in pattern"

    def test_redundancy_not_pejorative(self, card: dict):
        """Gombrich insists redundancy is necessary, not wasteful."""
        ri = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "redundancy_and_information")
        all_text = json.dumps(ri).lower()
        assert any(w in all_text for w in [
            "necessary", "reliab", "legib", "not waste",
        ]), "Card must note that redundancy is necessary, not wasteful"


class TestMonotonyVariety:
    """The monotony-variety tension is the central diagnostic."""

    def test_monotony_concept_present(self, card: dict):
        ids = {c["concept_id"] for c in card["core_concepts"]}
        assert "monotony_and_variety" in ids

    def test_mentions_restlessness_or_repose(self, card: dict):
        mv = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "monotony_and_variety")
        all_text = json.dumps(mv).lower()
        assert "restless" in all_text or "repose" in all_text or "restful" in all_text, (
            "Monotony/variety must discuss restlessness or repose"
        )

    def test_has_both_excess_indicators(self, card: dict):
        """Must describe both excessive monotony and excessive variety."""
        mv = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "monotony_and_variety")
        indicator_keys = set(mv.get("indicators", {}).keys())
        has_monotony = any("monoton" in k for k in indicator_keys)
        has_variety = any("variet" in k for k in indicator_keys)
        assert has_monotony and has_variety, (
            f"Need indicators for both excess monotony and excess variety, "
            f"have: {indicator_keys}"
        )


class TestGradingOfComplexity:
    """The complexity spectrum must include the key levels."""

    def test_grading_mentions_frieze_or_grid(self, card: dict):
        gc = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "grading_of_complexity")
        all_text = json.dumps(gc).lower()
        assert "frieze" in all_text or "grid" in all_text, (
            "Grading must mention simple repeat forms (frieze, grid)"
        )

    def test_grading_mentions_interlace(self, card: dict):
        gc = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "grading_of_complexity")
        all_text = json.dumps(gc).lower()
        assert "interlace" in all_text, "Grading must mention interlace"

    def test_grading_mentions_arabesque(self, card: dict):
        gc = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "grading_of_complexity")
        all_text = json.dumps(gc).lower()
        assert "arabesque" in all_text, "Grading must mention arabesque"

    def test_grading_mentions_grotesque(self, card: dict):
        gc = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "grading_of_complexity")
        all_text = json.dumps(gc).lower()
        assert "grotesque" in all_text, "Grading must mention grotesque"

    def test_complexity_not_hierarchy_of_value(self, card: dict):
        """More complex is not automatically better."""
        gc = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "grading_of_complexity")
        defn = gc["definition"].lower()
        assert any(phrase in defn for phrase in [
            "not a hierarchy of value", "not a hierarchy", "appropriate",
            "function", "context",
        ]), "Grading must note that complexity is not a value hierarchy"


class TestFrameAndFill:
    """Frame-fill relationship is a fundamental organizing principle."""

    def test_frame_fill_present(self, card: dict):
        ids = {c["concept_id"] for c in card["core_concepts"]}
        assert "frame_and_fill" in ids

    def test_frame_fill_mentions_corners(self, card: dict):
        ff = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "frame_and_fill")
        all_text = json.dumps(ff).lower()
        assert "corner" in all_text, (
            "Frame-fill must discuss corner solutions"
        )

    def test_frame_fill_mentions_hierarchy(self, card: dict):
        ff = next(c for c in card["core_concepts"]
                  if c["concept_id"] == "frame_and_fill")
        all_text = json.dumps(ff).lower()
        assert "hierarch" in all_text, (
            "Frame-fill must discuss hierarchical nesting"
        )


class TestEssentialClaims:
    """The card must preserve Gombrich's essential theoretical commitments."""

    def test_has_anti_goals(self, card: dict):
        goals = card.get("anti_goals", [])
        assert len(goals) >= 5, f"Need at least 5 anti-goals, have {len(goals)}"

    def test_anti_goals_reject_non_pattern_use(self, card: dict):
        """Must not be applied to images without pattern."""
        all_anti = " ".join(card.get("anti_goals", [])).lower()
        assert any(phrase in all_anti for phrase in [
            "without pattern", "without repetition", "figurative",
        ]), "Anti-goals must restrict framework to pattern/decorative art"

    def test_has_tensions(self, card: dict):
        tensions = card.get("tensions", [])
        assert len(tensions) >= 2, f"Need at least 2 tensions, have {len(tensions)}"

    def test_has_citations(self, card: dict):
        citations = card.get("citations", [])
        assert len(citations) >= 5, f"Need at least 5 citations, have {len(citations)}"

    def test_has_confidence_notes(self, card: dict):
        notes = card.get("confidence_notes", [])
        assert len(notes) >= 2, f"Need at least 2 confidence notes, have {len(notes)}"

    def test_thesis_mentions_sense_of_order(self, card: dict):
        thesis = card.get("thesis", "").lower()
        assert "sense of order" in thesis, "Thesis must mention the sense of order"

    def test_thesis_mentions_redundancy_or_information(self, card: dict):
        thesis = card.get("thesis", "").lower()
        assert "redundancy" in thesis or "information" in thesis, (
            "Thesis must mention redundancy or information"
        )


class TestDistinctiveVocabulary:
    """The card must use Gombrich's actual terms, not generic design language."""

    def test_uses_distinctive_terms(self, card: dict):
        text = json.dumps(card).lower()
        vocab = [v.lower() for v in gt.DISTINCTIVE_VOCABULARY]
        hits = [v for v in vocab if v in text]
        ratio = len(hits) / len(vocab)
        assert ratio >= 0.5, (
            f"Only {len(hits)}/{len(vocab)} ({ratio:.0%}) distinctive terms found. "
            f"Missing: {set(vocab) - set(hits)}"
        )

    def test_uses_key_gombrich_terms(self, card: dict):
        """These specific terms are non-negotiable for a Gombrich card."""
        text = json.dumps(card).lower()
        must_have = ["sense of order", "redundancy", "information",
                     "habituation", "frame and fill", "monotony"]
        missing = [t for t in must_have if t not in text]
        assert not missing, f"Missing essential Gombrich terms: {missing}"

    def test_generic_vocabulary_does_not_dominate(self, card: dict):
        from evals.fixtures.generic_baseline import GENERIC_VOCABULARY
        text = json.dumps(card).lower()
        distinctive_hits = sum(1 for v in gt.DISTINCTIVE_VOCABULARY if v.lower() in text)
        generic_hits = sum(1 for v in GENERIC_VOCABULARY if v.lower() in text)
        assert distinctive_hits >= generic_hits, (
            f"Generic vocabulary ({generic_hits}) outnumbers distinctive ({distinctive_hits})"
        )
