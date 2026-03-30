"""
Evaluate the Kandinsky critic card against ground truth.

Kandinsky's structure is element-based (point, line, basic_plane), NOT
bipolar like Wölfflin. These tests validate that the card preserves
Kandinsky's distinctive grammar of visual forces.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from evals.ground_truth import kandinsky as gt

CARD_PATH = Path(__file__).resolve().parent.parent / "critics" / "kandinsky.json"


@pytest.fixture
def card() -> dict:
    if not CARD_PATH.exists():
        pytest.skip("Kandinsky critic card not yet produced")
    return json.loads(CARD_PATH.read_text())


class TestElementCoverage:
    """All three elements must be present with full operational detail."""

    EXPECTED_ELEMENTS = {"point", "line", "basic_plane"}

    def test_has_all_three_elements(self, card: dict):
        element_ids = {e["element_id"] for e in card["elements"]}
        assert self.EXPECTED_ELEMENTS == element_ids, (
            f"Missing: {self.EXPECTED_ELEMENTS - element_ids}, "
            f"Extra: {element_ids - self.EXPECTED_ELEMENTS}"
        )

    def test_each_element_has_definition(self, card: dict):
        for elem in card["elements"]:
            assert "definition" in elem, f"{elem['element_id']} missing definition"
            assert len(elem["definition"]) >= 50, (
                f"{elem['element_id']} definition too short"
            )

    def test_each_element_has_properties(self, card: dict):
        for elem in card["elements"]:
            props = elem.get("properties", {})
            assert len(props) >= 2, (
                f"{elem['element_id']} needs at least 2 properties, has {len(props)}"
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
                f"{elem['element_id']} needs at least 2 indicator categories, has {len(indicators)}"
            )
            for cat, items in indicators.items():
                assert len(items) >= 2, (
                    f"{elem['element_id']}.indicators.{cat} needs at least 2 items"
                )

    def test_each_element_has_feedback_directions(self, card: dict):
        for elem in card["elements"]:
            fb = elem.get("feedback_directions", {})
            assert len(fb) >= 2, (
                f"{elem['element_id']} needs at least 2 feedback direction categories"
            )
            for direction, items in fb.items():
                assert len(items) >= 2, (
                    f"{elem['element_id']}.feedback_directions.{direction} needs at least 2 items"
                )

    def test_each_element_has_common_misreadings(self, card: dict):
        for elem in card["elements"]:
            misreadings = elem.get("common_misreadings", [])
            assert len(misreadings) >= 2, (
                f"{elem['element_id']} needs at least 2 common_misreadings"
            )


class TestTemperatureProperties:
    """Kandinsky's temperature system must be present — this is what makes
    his framework distinctive, not just geometric element-naming."""

    def test_line_has_temperature_by_direction(self, card: dict):
        line = next(e for e in card["elements"] if e["element_id"] == "line")
        props = line.get("properties", {})
        temp = props.get("temperature_by_direction", {})
        assert "horizontal" in temp, "Line must have horizontal temperature"
        assert "vertical" in temp, "Line must have vertical temperature"
        assert "diagonal" in temp, "Line must have diagonal temperature"

    def test_horizontal_is_cold(self, card: dict):
        line = next(e for e in card["elements"] if e["element_id"] == "line")
        h = line["properties"]["temperature_by_direction"]["horizontal"].lower()
        assert "cold" in h, f"Horizontal should be cold, got: {h}"

    def test_vertical_is_warm(self, card: dict):
        line = next(e for e in card["elements"] if e["element_id"] == "line")
        v = line["properties"]["temperature_by_direction"]["vertical"].lower()
        assert "warm" in v, f"Vertical should be warm, got: {v}"

    def test_bp_has_format_temperature(self, card: dict):
        bp = next(e for e in card["elements"] if e["element_id"] == "basic_plane")
        props = bp.get("properties", {})
        fmt = props.get("format_temperature", {})
        assert "square" in fmt, "BP must describe square format temperature"
        assert "horizontal" in fmt, "BP must describe horizontal format temperature"
        assert "vertical" in fmt, "BP must describe vertical format temperature"


class TestBPAsActive:
    """The basic plane must be treated as a living participant, not a neutral
    container. This is Kandinsky's most distinctive claim about the BP."""

    def test_bp_has_boundary_tensions(self, card: dict):
        bp = next(e for e in card["elements"] if e["element_id"] == "basic_plane")
        boundaries = bp.get("properties", {}).get("boundary_tensions", {})
        for zone in ["above", "below", "left", "right"]:
            assert zone in boundaries, f"BP missing boundary tension for '{zone}'"

    def test_above_is_light_below_is_heavy(self, card: dict):
        bp = next(e for e in card["elements"] if e["element_id"] == "basic_plane")
        boundaries = bp["properties"]["boundary_tensions"]
        above = boundaries["above"].lower()
        below = boundaries["below"].lower()
        assert any(w in above for w in ["light", "loose", "freedom", "emancipation"]), (
            f"'Above' should convey lightness/freedom, got: {above}"
        )
        assert any(w in below for w in ["heavy", "dense", "constraint", "condensation"]), (
            f"'Below' should convey heaviness/constraint, got: {below}"
        )

    def test_bp_described_as_active(self, card: dict):
        """The BP definition must positively describe it as active/living."""
        bp = next(e for e in card["elements"] if e["element_id"] == "basic_plane")
        definition = bp.get("definition", "").lower()
        assert any(w in definition for w in ["living", "active", "tension", "force"]), (
            "BP definition should describe it as living/active, not neutral"
        )


class TestCompositionalPrinciples:
    """Counterpoint, tension, and rhythm are the compositional logic."""

    def test_has_compositional_principles(self, card: dict):
        principles = card.get("compositional_principles", [])
        assert len(principles) >= 3, (
            f"Need at least 3 compositional principles, have {len(principles)}"
        )

    def test_counterpoint_present(self, card: dict):
        ids = {p["principle_id"] for p in card.get("compositional_principles", [])}
        assert "counterpoint" in ids, "Must include counterpoint as a principle"

    def test_tension_present(self, card: dict):
        ids = {p["principle_id"] for p in card.get("compositional_principles", [])}
        assert "tension" in ids, "Must include tension as a principle"

    def test_each_principle_has_diagnostic_questions(self, card: dict):
        for p in card.get("compositional_principles", []):
            qs = p.get("diagnostic_questions", [])
            assert len(qs) >= 1, (
                f"Principle '{p['principle_id']}' needs at least 1 diagnostic question"
            )


class TestEssentialClaims:
    """The card must preserve Kandinsky's essential theoretical commitments."""

    def test_has_anti_goals(self, card: dict):
        goals = card.get("anti_goals", [])
        assert len(goals) >= 5, f"Need at least 5 anti-goals, have {len(goals)}"

    def test_anti_goals_reject_shape_naming(self, card: dict):
        """The single most important anti-goal: don't just name shapes."""
        all_anti = " ".join(card.get("anti_goals", [])).lower()
        assert any(phrase in all_anti for phrase in [
            "naming", "geometric shapes", "name geometric", "circles, lines",
        ]), "Anti-goals must explicitly reject reducing analysis to naming shapes"

    def test_has_tensions(self, card: dict):
        tensions = card.get("tensions", [])
        assert len(tensions) >= 2, f"Need at least 2 tensions, have {len(tensions)}"

    def test_has_citations(self, card: dict):
        citations = card.get("citations", [])
        assert len(citations) >= 5, f"Need at least 5 citations, have {len(citations)}"

    def test_has_confidence_notes(self, card: dict):
        notes = card.get("confidence_notes", [])
        assert len(notes) >= 2, f"Need at least 2 confidence notes, have {len(notes)}"


class TestDistinctiveVocabulary:
    """The card must use Kandinsky's actual terms, not generic design language."""

    def test_uses_distinctive_terms(self, card: dict):
        text = json.dumps(card).lower()
        vocab = [v.lower() for v in gt.DISTINCTIVE_VOCABULARY]
        hits = [v for v in vocab if v in text]
        ratio = len(hits) / len(vocab)
        assert ratio >= 0.5, (
            f"Only {len(hits)}/{len(vocab)} ({ratio:.0%}) distinctive terms found. "
            f"Missing: {set(vocab) - set(hits)}"
        )

    def test_uses_key_kandinsky_terms(self, card: dict):
        """These specific terms are non-negotiable for a Kandinsky card."""
        text = json.dumps(card).lower()
        must_have = ["tension", "counterpoint", "warm", "cold", "basic plane", "concentric"]
        missing = [t for t in must_have if t not in text]
        assert not missing, f"Missing essential Kandinsky terms: {missing}"

    def test_generic_vocabulary_does_not_dominate(self, card: dict):
        from evals.fixtures.generic_baseline import GENERIC_VOCABULARY
        text = json.dumps(card).lower()
        distinctive_hits = sum(1 for v in gt.DISTINCTIVE_VOCABULARY if v.lower() in text)
        generic_hits = sum(1 for v in GENERIC_VOCABULARY if v.lower() in text)
        assert distinctive_hits >= generic_hits, (
            f"Generic vocabulary ({generic_hits}) outnumbers distinctive ({distinctive_hits})"
        )
