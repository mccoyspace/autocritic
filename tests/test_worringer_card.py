"""
Evaluate the Worringer critic card against ground truth.

Worringer's framework is bipolar but with only ONE axis: empathy vs.
abstraction. These are not style labels but deep psychic orientations.
The most distinctive features are: the psychological basis (dread vs.
confidence), the spatial diagnostic (depth vs. planarity), and the
concept of artistic volition (Kunstwollen).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from evals.ground_truth import worringer as gt

CARD_PATH = Path(__file__).resolve().parent.parent / "critics" / "worringer.json"


@pytest.fixture
def card() -> dict:
    if not CARD_PATH.exists():
        pytest.skip("Worringer critic card not yet produced")
    return json.loads(CARD_PATH.read_text())


class TestImpulseCoverage:
    """Both impulses must be present with full operational detail."""

    EXPECTED_IMPULSES = {"empathy", "abstraction"}

    def test_has_both_impulses(self, card: dict):
        impulse_ids = {i["impulse_id"] for i in card["impulses"]}
        assert self.EXPECTED_IMPULSES == impulse_ids, (
            f"Missing: {self.EXPECTED_IMPULSES - impulse_ids}, "
            f"Extra: {impulse_ids - self.EXPECTED_IMPULSES}"
        )

    def test_each_impulse_has_definition(self, card: dict):
        for imp in card["impulses"]:
            assert "definition" in imp, f"{imp['impulse_id']} missing definition"
            assert len(imp["definition"]) >= 50, (
                f"{imp['impulse_id']} definition too short"
            )

    def test_each_impulse_has_psychological_basis(self, card: dict):
        for imp in card["impulses"]:
            assert "psychological_basis" in imp, (
                f"{imp['impulse_id']} missing psychological_basis"
            )
            assert len(imp["psychological_basis"]) >= 30, (
                f"{imp['impulse_id']} psychological_basis too short"
            )

    def test_each_impulse_has_art_character(self, card: dict):
        for imp in card["impulses"]:
            chars = imp.get("art_character", [])
            assert len(chars) >= 3, (
                f"{imp['impulse_id']} needs at least 3 art_character items, has {len(chars)}"
            )

    def test_each_impulse_has_diagnostic_questions(self, card: dict):
        for imp in card["impulses"]:
            qs = imp.get("diagnostic_questions", [])
            assert len(qs) >= 3, (
                f"{imp['impulse_id']} needs at least 3 diagnostic questions, has {len(qs)}"
            )

    def test_each_impulse_has_indicators(self, card: dict):
        for imp in card["impulses"]:
            indicators = imp.get("indicators", {})
            assert len(indicators) >= 2, (
                f"{imp['impulse_id']} needs at least 2 indicator categories"
            )
            for cat, items in indicators.items():
                assert len(items) >= 2, (
                    f"{imp['impulse_id']}.indicators.{cat} needs >= 2 items"
                )

    def test_each_impulse_has_feedback_directions(self, card: dict):
        for imp in card["impulses"]:
            fb = imp.get("feedback_directions", {})
            assert len(fb) >= 2, (
                f"{imp['impulse_id']} needs at least 2 feedback direction categories"
            )

    def test_each_impulse_has_common_misreadings(self, card: dict):
        for imp in card["impulses"]:
            misreadings = imp.get("common_misreadings", [])
            assert len(misreadings) >= 2, (
                f"{imp['impulse_id']} needs at least 2 common_misreadings"
            )


class TestPsychologicalBasis:
    """The psychological dimension is what makes Worringer distinctive —
    not just abstract vs. realistic but dread vs. confidence."""

    def test_empathy_mentions_confidence(self, card: dict):
        emp = next(i for i in card["impulses"] if i["impulse_id"] == "empathy")
        basis = emp["psychological_basis"].lower()
        assert "confidence" in basis, (
            "Empathy's psychological basis must mention confidence"
        )

    def test_empathy_mentions_pantheistic(self, card: dict):
        emp = next(i for i in card["impulses"] if i["impulse_id"] == "empathy")
        all_text = json.dumps(emp).lower()
        assert "pantheistic" in all_text, (
            "Empathy must mention pantheistic relationship"
        )

    def test_abstraction_mentions_dread(self, card: dict):
        abst = next(i for i in card["impulses"] if i["impulse_id"] == "abstraction")
        all_text = json.dumps(abst).lower()
        assert "dread" in all_text, (
            "Abstraction must mention dread of space"
        )

    def test_abstraction_mentions_flux(self, card: dict):
        abst = next(i for i in card["impulses"] if i["impulse_id"] == "abstraction")
        all_text = json.dumps(abst).lower()
        assert "flux" in all_text, (
            "Abstraction must mention flux of being"
        )

    def test_abstraction_not_lack_of_ability(self, card: dict):
        """Worringer's central claim: abstraction is volition, not deficiency."""
        all_text = json.dumps(card).lower()
        assert any(phrase in all_text for phrase in [
            "not a lack", "not a deficiency", "differently directed",
            "not failed", "volition",
        ]), "Card must state that abstraction is not a lack of ability"


class TestSpaceDiagnostic:
    """Space is the major enemy of abstraction — treatment of space
    is the single most diagnostic visual property."""

    def test_space_mentioned_in_abstraction(self, card: dict):
        abst = next(i for i in card["impulses"] if i["impulse_id"] == "abstraction")
        defn = abst["definition"].lower()
        assert "space" in defn, "Abstraction definition must mention space"

    def test_space_as_enemy(self, card: dict):
        all_text = json.dumps(card).lower()
        assert "enemy" in all_text or "suppress" in all_text, (
            "Card must describe space as the enemy of abstraction / to be suppressed"
        )

    def test_depth_suppression_in_abstraction(self, card: dict):
        abst = next(i for i in card["impulses"] if i["impulse_id"] == "abstraction")
        all_text = json.dumps(abst).lower()
        assert "depth" in all_text and "suppress" in all_text, (
            "Abstraction must discuss suppression of depth"
        )

    def test_depth_embrace_in_empathy(self, card: dict):
        emp = next(i for i in card["impulses"] if i["impulse_id"] == "empathy")
        all_text = json.dumps(emp).lower()
        assert "depth" in all_text or "spatial" in all_text or "illusionism" in all_text, (
            "Empathy must discuss spatial depth or illusionism"
        )


class TestKunstwollen:
    """Artistic volition (Kunstwollen) must be present — style reflects
    psychic need, not ability."""

    def test_mentions_kunstwollen(self, card: dict):
        text = json.dumps(card).lower()
        assert "kunstwollen" in text, "Card must mention Kunstwollen"

    def test_mentions_artistic_volition(self, card: dict):
        text = json.dumps(card).lower()
        assert "artistic volition" in text or "volition" in text, (
            "Card must discuss artistic volition"
        )

    def test_has_volition_diagnostic_dimension(self, card: dict):
        dims = card.get("diagnostic_dimensions", [])
        dim_ids = {d.get("dimension_id", "") for d in dims}
        assert "artistic_volition" in dim_ids, (
            "Must have artistic_volition as a diagnostic dimension"
        )


class TestCoreDiagnostic:
    """The card must include the core diagnostic question."""

    def test_has_core_diagnostic(self, card: dict):
        diag = card.get("core_diagnostic", "")
        assert len(diag) >= 50, "Core diagnostic must be substantial"

    def test_core_diagnostic_mentions_flux(self, card: dict):
        diag = card.get("core_diagnostic", "").lower()
        assert "flux" in diag, "Core diagnostic must mention the flux of the visible world"

    def test_core_diagnostic_mentions_coherence(self, card: dict):
        diag = card.get("core_diagnostic", "").lower()
        assert "coher" in diag, "Core diagnostic must ask about coherence of stance"

    def test_has_diagnostic_dimensions(self, card: dict):
        dims = card.get("diagnostic_dimensions", [])
        assert len(dims) >= 2, f"Need at least 2 diagnostic dimensions, have {len(dims)}"

    def test_has_stance_coherence_dimension(self, card: dict):
        dims = card.get("diagnostic_dimensions", [])
        dim_ids = {d.get("dimension_id", "") for d in dims}
        assert "stance_coherence" in dim_ids, (
            "Must have stance_coherence as a diagnostic dimension"
        )

    def test_has_space_treatment_dimension(self, card: dict):
        dims = card.get("diagnostic_dimensions", [])
        dim_ids = {d.get("dimension_id", "") for d in dims}
        assert "space_treatment" in dim_ids, (
            "Must have space_treatment as a diagnostic dimension"
        )


class TestGothicSynthesis:
    """The Gothic third way must be acknowledged — heightened expression
    on an inorganic fundament."""

    def test_mentions_gothic(self, card: dict):
        text = json.dumps(card).lower()
        assert "gothic" in text, "Card must mention the Gothic synthesis"

    def test_mentions_inorganic_fundament(self, card: dict):
        text = json.dumps(card).lower()
        assert "inorganic" in text, (
            "Card must mention the inorganic fundament"
        )

    def test_gothic_not_confused_middle(self, card: dict):
        """Gothic is a distinct synthesis, not an unresolved wavering."""
        text = json.dumps(card).lower()
        assert any(phrase in text for phrase in [
            "synthesis", "third", "heightened expression",
        ]), "Card must present Gothic as a distinct position, not a confused middle"


class TestEssentialClaims:
    """The card must preserve Worringer's essential theoretical commitments."""

    def test_has_anti_goals(self, card: dict):
        goals = card.get("anti_goals", [])
        assert len(goals) >= 5, f"Need at least 5 anti-goals, have {len(goals)}"

    def test_anti_goals_reject_skill_grading(self, card: dict):
        all_anti = " ".join(card.get("anti_goals", [])).lower()
        assert any(phrase in all_anti for phrase in [
            "skill", "ability", "accuracy",
        ]), "Anti-goals must reject grading on skill or accuracy"

    def test_anti_goals_reject_empathy_superiority(self, card: dict):
        """Neither impulse is superior."""
        all_anti = " ".join(card.get("anti_goals", [])).lower()
        assert any(phrase in all_anti for phrase in [
            "neither", "not superior", "prejudice", "vice versa",
        ]), "Anti-goals must reject treating either impulse as superior"

    def test_has_tensions(self, card: dict):
        tensions = card.get("tensions", [])
        assert len(tensions) >= 2, f"Need at least 2 tensions, have {len(tensions)}"

    def test_has_citations(self, card: dict):
        citations = card.get("citations", [])
        assert len(citations) >= 5, f"Need at least 5 citations, have {len(citations)}"

    def test_has_confidence_notes(self, card: dict):
        notes = card.get("confidence_notes", [])
        assert len(notes) >= 2, f"Need at least 2 confidence notes, have {len(notes)}"

    def test_thesis_mentions_empathy_and_abstraction(self, card: dict):
        thesis = card.get("thesis", "").lower()
        assert "empathy" in thesis and "abstraction" in thesis, (
            "Thesis must mention both empathy and abstraction"
        )


class TestDistinctiveVocabulary:
    """The card must use Worringer's actual terms, not generic art language."""

    def test_uses_distinctive_terms(self, card: dict):
        text = json.dumps(card).lower()
        vocab = [v.lower() for v in gt.DISTINCTIVE_VOCABULARY]
        hits = [v for v in vocab if v in text]
        ratio = len(hits) / len(vocab)
        assert ratio >= 0.5, (
            f"Only {len(hits)}/{len(vocab)} ({ratio:.0%}) distinctive terms found. "
            f"Missing: {set(vocab) - set(hits)}"
        )

    def test_uses_key_worringer_terms(self, card: dict):
        """These specific terms are non-negotiable for a Worringer card."""
        text = json.dumps(card).lower()
        must_have = ["einfühlung", "kunstwollen", "dread",
                     "crystalline", "flux", "pantheistic"]
        # Handle JSON unicode escaping for ü
        must_have_escaped = [t.replace("ü", "\\u00fc") for t in must_have]
        missing = [t for t, te in zip(must_have, must_have_escaped)
                   if t not in text and te not in text]
        assert not missing, f"Missing essential Worringer terms: {missing}"

    def test_generic_vocabulary_does_not_dominate(self, card: dict):
        from evals.fixtures.generic_baseline import GENERIC_VOCABULARY
        text = json.dumps(card).lower()
        distinctive_hits = sum(1 for v in gt.DISTINCTIVE_VOCABULARY if v.lower() in text)
        generic_hits = sum(1 for v in GENERIC_VOCABULARY if v.lower() in text)
        assert distinctive_hits >= generic_hits, (
            f"Generic vocabulary ({generic_hits}) outnumbers distinctive ({distinctive_hits})"
        )
