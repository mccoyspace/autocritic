"""
Evaluate the Arnheim critic card against ground truth.

Arnheim's structure is a progressive hierarchy of perceptual principles:
balance → simplicity → dynamics → expression. The most distinctive feature
is the force/tension language — visual properties are perceptual forces,
not static attributes. Expression is not separate from form; it IS form
perceived as force.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from evals.ground_truth import arnheim as gt

CARD_PATH = Path(__file__).resolve().parent.parent / "critics" / "arnheim.json"


@pytest.fixture
def card() -> dict:
    if not CARD_PATH.exists():
        pytest.skip("Arnheim critic card not yet produced")
    return json.loads(CARD_PATH.read_text())


class TestPrincipleCoverage:
    """All four principles must be present with progressive ordering."""

    EXPECTED_PRINCIPLES = {"balance", "simplicity", "dynamics", "expression"}

    def test_has_all_four_principles(self, card: dict):
        principle_ids = {p["principle_id"] for p in card["principles"]}
        assert self.EXPECTED_PRINCIPLES == principle_ids, (
            f"Missing: {self.EXPECTED_PRINCIPLES - principle_ids}, "
            f"Extra: {principle_ids - self.EXPECTED_PRINCIPLES}"
        )

    def test_principles_have_progression_order(self, card: dict):
        """Balance < Simplicity < Dynamics < Expression in Arnheim's hierarchy."""
        order = {p["principle_id"]: p.get("progression_order", 0)
                 for p in card["principles"]}
        assert order["balance"] < order["simplicity"] < order["dynamics"] < order["expression"], (
            f"Wrong progression: balance={order['balance']}, simplicity={order['simplicity']}, "
            f"dynamics={order['dynamics']}, expression={order['expression']}"
        )

    def test_each_principle_has_definition(self, card: dict):
        for p in card["principles"]:
            assert "definition" in p, f"{p['principle_id']} missing definition"
            assert len(p["definition"]) >= 50, (
                f"{p['principle_id']} definition too short"
            )

    def test_each_principle_has_diagnostic_questions(self, card: dict):
        for p in card["principles"]:
            qs = p.get("diagnostic_questions", [])
            assert len(qs) >= 3, (
                f"{p['principle_id']} needs at least 3 diagnostic questions, has {len(qs)}"
            )

    def test_each_principle_has_indicators(self, card: dict):
        for p in card["principles"]:
            indicators = p.get("indicators", {})
            assert len(indicators) >= 2, (
                f"{p['principle_id']} needs at least 2 indicator categories"
            )
            for cat, items in indicators.items():
                assert len(items) >= 2, (
                    f"{p['principle_id']}.indicators.{cat} needs >= 2 items"
                )

    def test_each_principle_has_feedback_directions(self, card: dict):
        for p in card["principles"]:
            fb = p.get("feedback_directions", {})
            assert len(fb) >= 2, (
                f"{p['principle_id']} needs at least 2 feedback direction categories"
            )

    def test_each_principle_has_common_misreadings(self, card: dict):
        for p in card["principles"]:
            misreadings = p.get("common_misreadings", [])
            assert len(misreadings) >= 2, (
                f"{p['principle_id']} needs at least 2 common_misreadings"
            )

    def test_each_principle_has_key_concepts(self, card: dict):
        for p in card["principles"]:
            concepts = p.get("key_concepts", [])
            assert len(concepts) >= 3, (
                f"{p['principle_id']} needs at least 3 key_concepts, has {len(concepts)}"
            )


class TestForceLanguage:
    """Arnheim's most distinctive move: visual properties as perceptual forces.
    The card must use force/tension language throughout, not static attributes."""

    def test_balance_mentions_forces(self, card: dict):
        balance = next(p for p in card["principles"] if p["principle_id"] == "balance")
        defn = balance["definition"].lower()
        assert "force" in defn, "Balance definition must mention forces"

    def test_balance_mentions_equilibrium(self, card: dict):
        balance = next(p for p in card["principles"] if p["principle_id"] == "balance")
        defn = balance["definition"].lower()
        assert "equilibrium" in defn, "Balance definition must mention equilibrium"

    def test_balance_mentions_visual_weight(self, card: dict):
        balance = next(p for p in card["principles"] if p["principle_id"] == "balance")
        all_text = json.dumps(balance).lower()
        assert "visual weight" in all_text or "weight" in all_text, (
            "Balance must discuss visual weight"
        )

    def test_dynamics_mentions_directed_tension(self, card: dict):
        dynamics = next(p for p in card["principles"] if p["principle_id"] == "dynamics")
        defn = dynamics["definition"].lower()
        assert "directed tension" in defn, (
            "Dynamics definition must mention directed tension"
        )

    def test_dynamics_mentions_deformation(self, card: dict):
        dynamics = next(p for p in card["principles"] if p["principle_id"] == "dynamics")
        all_text = json.dumps(dynamics).lower()
        assert "deformation" in all_text, "Dynamics must discuss deformation as source of tension"

    def test_dynamics_mentions_obliqueness(self, card: dict):
        dynamics = next(p for p in card["principles"] if p["principle_id"] == "dynamics")
        all_text = json.dumps(dynamics).lower()
        assert "oblique" in all_text, "Dynamics must discuss obliqueness"

    def test_dynamics_not_just_movement(self, card: dict):
        """Dynamics is perceived force, not depicted movement."""
        dynamics = next(p for p in card["principles"] if p["principle_id"] == "dynamics")
        defn = dynamics["definition"].lower()
        assert "not" in defn and "movement" in defn, (
            "Dynamics definition must distinguish from depicted movement"
        )


class TestSimplicityPragnanz:
    """Simplicity must be grounded in Prägnanz, not just 'less is more'."""

    def test_simplicity_mentions_pragnanz(self, card: dict):
        simplicity = next(p for p in card["principles"] if p["principle_id"] == "simplicity")
        all_text = json.dumps(simplicity).lower()
        assert "prägnanz" in all_text or "pragnanz" in all_text or "pr\\u00e4gnanz" in all_text, (
            "Simplicity must mention Prägnanz"
        )

    def test_simplicity_mentions_structural_skeleton(self, card: dict):
        simplicity = next(p for p in card["principles"] if p["principle_id"] == "simplicity")
        all_text = json.dumps(simplicity).lower()
        assert "structural skeleton" in all_text, (
            "Simplicity must discuss the structural skeleton"
        )

    def test_simplicity_mentions_leveling_sharpening(self, card: dict):
        simplicity = next(p for p in card["principles"] if p["principle_id"] == "simplicity")
        all_text = json.dumps(simplicity).lower()
        assert "leveling" in all_text and "sharpening" in all_text, (
            "Simplicity must discuss both leveling and sharpening"
        )


class TestExpressionEmbedded:
    """Expression must be treated as embedded in form, not separate from it."""

    def test_expression_not_projected(self, card: dict):
        expression = next(p for p in card["principles"] if p["principle_id"] == "expression")
        defn = expression["definition"].lower()
        assert "not projected" in defn or "not project" in defn, (
            "Expression definition must state it is not projected onto forms"
        )

    def test_expression_mentions_physiognomic(self, card: dict):
        expression = next(p for p in card["principles"] if p["principle_id"] == "expression")
        all_text = json.dumps(expression).lower()
        assert "physiognomic" in all_text, (
            "Expression must mention physiognomic perception"
        )

    def test_expression_mentions_isomorphism(self, card: dict):
        expression = next(p for p in card["principles"] if p["principle_id"] == "expression")
        all_text = json.dumps(expression).lower()
        assert "isomorphism" in all_text, (
            "Expression must mention isomorphism (structural kinship)"
        )

    def test_expression_arises_from_dynamics(self, card: dict):
        """Expression is not separate from dynamics — it IS dynamics as meaning."""
        expression = next(p for p in card["principles"] if p["principle_id"] == "expression")
        all_text = json.dumps(expression).lower()
        assert "dynamics" in all_text or "dynamic" in all_text or "tension" in all_text, (
            "Expression must connect to dynamics/tension"
        )


class TestEssentialClaims:
    """The card must preserve Arnheim's essential theoretical commitments."""

    def test_has_anti_goals(self, card: dict):
        goals = card.get("anti_goals", [])
        assert len(goals) >= 5, f"Need at least 5 anti-goals, have {len(goals)}"

    def test_anti_goals_reject_static_attributes(self, card: dict):
        """The most important anti-goal: not static attributes but forces."""
        all_anti = " ".join(card.get("anti_goals", [])).lower()
        assert any(phrase in all_anti for phrase in [
            "static", "force", "tension",
        ]), "Anti-goals must reject treating visual properties as static attributes"

    def test_anti_goals_reject_expression_form_split(self, card: dict):
        all_anti = " ".join(card.get("anti_goals", [])).lower()
        assert "expression" in all_anti and "form" in all_anti, (
            "Anti-goals must reject separating expression from form"
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
        assert "perception" in thesis, "Thesis must mention perception"

    def test_thesis_mentions_forces_or_tensions(self, card: dict):
        thesis = card.get("thesis", "").lower()
        assert "force" in thesis or "tension" in thesis, (
            "Thesis must mention forces or tensions"
        )


class TestDistinctiveVocabulary:
    """The card must use Arnheim's actual terms, not generic design language."""

    def test_uses_distinctive_terms(self, card: dict):
        text = json.dumps(card).lower()
        vocab = [v.lower() for v in gt.DISTINCTIVE_VOCABULARY]
        hits = [v for v in vocab if v in text]
        ratio = len(hits) / len(vocab)
        assert ratio >= 0.5, (
            f"Only {len(hits)}/{len(vocab)} ({ratio:.0%}) distinctive terms found. "
            f"Missing: {set(vocab) - set(hits)}"
        )

    def test_uses_key_arnheim_terms(self, card: dict):
        """These specific terms are non-negotiable for an Arnheim card."""
        text = json.dumps(card).lower()
        must_have = ["perceptual forces", "visual weight", "structural skeleton",
                     "directed tension", "obliqueness", "physiognomic"]
        missing = [t for t in must_have if t not in text]
        assert not missing, f"Missing essential Arnheim terms: {missing}"

    def test_generic_vocabulary_does_not_dominate(self, card: dict):
        from evals.fixtures.generic_baseline import GENERIC_VOCABULARY
        text = json.dumps(card).lower()
        distinctive_hits = sum(1 for v in gt.DISTINCTIVE_VOCABULARY if v.lower() in text)
        generic_hits = sum(1 for v in GENERIC_VOCABULARY if v.lower() in text)
        assert distinctive_hits >= generic_hits, (
            f"Generic vocabulary ({generic_hits}) outnumbers distinctive ({distinctive_hits})"
        )
