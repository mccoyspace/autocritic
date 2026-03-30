"""
Evaluate the Dow critic card against ground truth.

Dow's structure combines three elements (Line, Notan, Color) in a
progressive hierarchy with five principles of harmony-building. The
most distinctive feature is notan — this must be treated as the
backbone of his system.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from evals.ground_truth import dow as gt

CARD_PATH = Path(__file__).resolve().parent.parent / "critics" / "dow.json"


@pytest.fixture
def card() -> dict:
    if not CARD_PATH.exists():
        pytest.skip("Dow critic card not yet produced")
    return json.loads(CARD_PATH.read_text())


class TestElementCoverage:
    """All three elements must be present with progressive ordering."""

    EXPECTED_ELEMENTS = {"line", "notan", "color"}

    def test_has_all_three_elements(self, card: dict):
        element_ids = {e["element_id"] for e in card["elements"]}
        assert self.EXPECTED_ELEMENTS == element_ids, (
            f"Missing: {self.EXPECTED_ELEMENTS - element_ids}, "
            f"Extra: {element_ids - self.EXPECTED_ELEMENTS}"
        )

    def test_elements_have_progression_order(self, card: dict):
        """Line < Notan < Color in Dow's hierarchy."""
        order = {e["element_id"]: e.get("progression_order", 0)
                 for e in card["elements"]}
        assert order["line"] < order["notan"] < order["color"], (
            f"Wrong progression: line={order['line']}, notan={order['notan']}, "
            f"color={order['color']}"
        )

    def test_each_element_has_definition(self, card: dict):
        for elem in card["elements"]:
            assert "definition" in elem, f"{elem['element_id']} missing definition"
            assert len(elem["definition"]) >= 50, (
                f"{elem['element_id']} definition too short"
            )

    def test_each_element_has_diagnostic_questions(self, card: dict):
        for elem in card["elements"]:
            qs = elem.get("diagnostic_questions", [])
            assert len(qs) >= 3, (
                f"{elem['element_id']} needs at least 3 diagnostic questions, has {len(qs)}"
            )

    def test_each_element_has_indicators(self, card: dict):
        for elem in card["elements"]:
            indicators = elem.get("indicators", {})
            assert len(indicators) >= 2, (
                f"{elem['element_id']} needs at least 2 indicator categories"
            )
            for cat, items in indicators.items():
                assert len(items) >= 2, (
                    f"{elem['element_id']}.indicators.{cat} needs >= 2 items"
                )

    def test_each_element_has_feedback_directions(self, card: dict):
        for elem in card["elements"]:
            fb = elem.get("feedback_directions", {})
            assert len(fb) >= 2, (
                f"{elem['element_id']} needs at least 2 feedback direction categories"
            )

    def test_each_element_has_common_misreadings(self, card: dict):
        for elem in card["elements"]:
            misreadings = elem.get("common_misreadings", [])
            assert len(misreadings) >= 2, (
                f"{elem['element_id']} needs at least 2 common_misreadings"
            )


class TestNotanCentrality:
    """Notan is Dow's most distinctive concept. It must be treated as
    the backbone, not as a secondary concern."""

    def test_notan_definition_mentions_japanese(self, card: dict):
        notan = next(e for e in card["elements"] if e["element_id"] == "notan")
        defn = notan["definition"].lower()
        assert "japanese" in defn, "Notan definition must mention Japanese origin"

    def test_notan_definition_mentions_dark_light(self, card: dict):
        notan = next(e for e in card["elements"] if e["element_id"] == "notan")
        defn = notan["definition"].lower()
        assert "dark" in defn and "light" in defn, (
            "Notan definition must mention dark-light"
        )

    def test_notan_distinct_from_shadow(self, card: dict):
        """Dow insists notan ≠ light-and-shadow. The card must reflect this."""
        notan = next(e for e in card["elements"] if e["element_id"] == "notan")
        all_text = json.dumps(notan).lower()
        # Should mention the distinction somewhere
        assert any(phrase in all_text for phrase in [
            "not be confused", "not be mistaken", "must not be confounded",
            "independent of", "not light-and-shadow", "not shadow",
            "not recording", "not merely",
        ]), "Card must distinguish notan from light-and-shadow"

    def test_notan_mentions_two_value(self, card: dict):
        notan = next(e for e in card["elements"] if e["element_id"] == "notan")
        all_text = json.dumps(notan).lower()
        assert "two-value" in all_text or "two value" in all_text, (
            "Notan must discuss the two-value foundation"
        )

    def test_notan_mentions_massing(self, card: dict):
        notan = next(e for e in card["elements"] if e["element_id"] == "notan")
        all_text = json.dumps(notan).lower()
        assert "mass" in all_text, "Notan must discuss massing of dark and light"

    def test_color_subordinate_to_notan(self, card: dict):
        """Color must be described as dependent on / subordinate to notan."""
        color = next(e for e in card["elements"] if e["element_id"] == "color")
        defn = color["definition"].lower()
        assert any(w in defn for w in ["subordinate", "dependent", "built on"]), (
            "Color definition must express subordination to notan"
        )


class TestPrinciplesCoverage:
    """All five principles of harmony-building must be present."""

    EXPECTED_PRINCIPLES = {"opposition", "transition", "subordination",
                           "repetition", "symmetry"}

    def test_has_all_five_principles(self, card: dict):
        principle_ids = {p["principle_id"] for p in card.get("principles", [])}
        assert self.EXPECTED_PRINCIPLES == principle_ids, (
            f"Missing: {self.EXPECTED_PRINCIPLES - principle_ids}, "
            f"Extra: {principle_ids - self.EXPECTED_PRINCIPLES}"
        )

    def test_each_principle_has_definition(self, card: dict):
        for p in card.get("principles", []):
            assert "definition" in p, f"{p['principle_id']} missing definition"
            assert len(p["definition"]) >= 30, (
                f"{p['principle_id']} definition too short"
            )

    def test_has_overarching_principle(self, card: dict):
        """Proportion / Good Spacing must be present as the governing principle."""
        op = card.get("overarching_principle", {})
        assert op, "Must have an overarching_principle (Proportion / Good Spacing)"
        label = op.get("label", "").lower()
        assert "spacing" in label or "proportion" in label, (
            f"Overarching principle should be about spacing/proportion, got: {label}"
        )


class TestEssentialClaims:
    """The card must preserve Dow's essential theoretical commitments."""

    def test_has_anti_goals(self, card: dict):
        goals = card.get("anti_goals", [])
        assert len(goals) >= 5, f"Need at least 5 anti-goals, have {len(goals)}"

    def test_anti_goals_reject_imitation(self, card: dict):
        """Dow's most forceful claim: design before imitation."""
        all_anti = " ".join(card.get("anti_goals", [])).lower()
        assert any(phrase in all_anti for phrase in [
            "imitat", "representat", "accuracy",
        ]), "Anti-goals must reject representation/imitation as primary criterion"

    def test_has_tensions(self, card: dict):
        tensions = card.get("tensions", [])
        assert len(tensions) >= 2, f"Need at least 2 tensions, have {len(tensions)}"

    def test_has_citations(self, card: dict):
        citations = card.get("citations", [])
        assert len(citations) >= 5, f"Need at least 5 citations, have {len(citations)}"

    def test_has_confidence_notes(self, card: dict):
        notes = card.get("confidence_notes", [])
        assert len(notes) >= 2, f"Need at least 2 confidence notes, have {len(notes)}"

    def test_thesis_mentions_harmony_building(self, card: dict):
        thesis = card.get("thesis", "").lower()
        assert "harmony" in thesis, "Thesis must mention harmony-building"


class TestDistinctiveVocabulary:
    """The card must use Dow's actual terms, not generic design language."""

    def test_uses_distinctive_terms(self, card: dict):
        text = json.dumps(card).lower()
        vocab = [v.lower() for v in gt.DISTINCTIVE_VOCABULARY]
        hits = [v for v in vocab if v in text]
        ratio = len(hits) / len(vocab)
        assert ratio >= 0.5, (
            f"Only {len(hits)}/{len(vocab)} ({ratio:.0%}) distinctive terms found. "
            f"Missing: {set(vocab) - set(hits)}"
        )

    def test_uses_key_dow_terms(self, card: dict):
        """These specific terms are non-negotiable for a Dow card."""
        text = json.dumps(card).lower()
        must_have = ["notan", "dark-and-light", "spacing", "subordination",
                     "massing", "two-value"]
        missing = [t for t in must_have if t not in text]
        assert not missing, f"Missing essential Dow terms: {missing}"

    def test_generic_vocabulary_does_not_dominate(self, card: dict):
        from evals.fixtures.generic_baseline import GENERIC_VOCABULARY
        text = json.dumps(card).lower()
        distinctive_hits = sum(1 for v in gt.DISTINCTIVE_VOCABULARY if v.lower() in text)
        generic_hits = sum(1 for v in GENERIC_VOCABULARY if v.lower() in text)
        assert distinctive_hits >= generic_hits, (
            f"Generic vocabulary ({generic_hits}) outnumbers distinctive ({distinctive_hits})"
        )
