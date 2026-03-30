"""
Tests that the ground-truth modules themselves are well-formed.

These run without an API key — they validate that our hand-written
knowledge about each theory is internally consistent and complete.
"""

import pytest
from evals.ground_truth import THEORISTS


REQUIRED_ATTRS = [
    "ESSENTIAL_CLAIMS",
    "ANTI_GOALS",
    "DISTINCTIVE_VOCABULARY",
    "GOOD_CRITIQUE_EXAMPLE",
    "BAD_CRITIQUE_EXAMPLE",
]


@pytest.mark.parametrize("name", list(THEORISTS.keys()))
class TestGroundTruthCompleteness:
    """Every ground-truth module must have the core attributes."""

    def test_has_required_attrs(self, name: str):
        mod = THEORISTS[name]
        for attr in REQUIRED_ATTRS:
            assert hasattr(mod, attr), f"{name} missing {attr}"

    def test_essential_claims_non_empty(self, name: str):
        claims = THEORISTS[name].ESSENTIAL_CLAIMS
        assert len(claims) >= 3, f"{name} needs at least 3 essential claims"

    def test_anti_goals_non_empty(self, name: str):
        goals = THEORISTS[name].ANTI_GOALS
        assert len(goals) >= 3, f"{name} needs at least 3 anti-goals"

    def test_distinctive_vocabulary_non_empty(self, name: str):
        vocab = THEORISTS[name].DISTINCTIVE_VOCABULARY
        assert len(vocab) >= 8, f"{name} needs at least 8 distinctive terms"

    def test_good_and_bad_examples_differ(self, name: str):
        mod = THEORISTS[name]
        good = mod.GOOD_CRITIQUE_EXAMPLE.lower()
        bad = mod.BAD_CRITIQUE_EXAMPLE.lower()
        # The good example should use distinctive vocabulary
        vocab = [v.lower() for v in mod.DISTINCTIVE_VOCABULARY]
        good_hits = sum(1 for v in vocab if v in good)
        bad_hits = sum(1 for v in vocab if v in bad)
        assert good_hits > bad_hits, (
            f"{name}: good example should use more distinctive vocabulary "
            f"than bad example (good={good_hits}, bad={bad_hits})"
        )


class TestVocabularyOverlap:
    """Distinctive vocabularies should be meaningfully different across theorists."""

    def test_pairwise_overlap_is_limited(self):
        """No two theorists should share more than 30% of their vocabulary."""
        names = list(THEORISTS.keys())
        for i, name_a in enumerate(names):
            vocab_a = set(v.lower() for v in THEORISTS[name_a].DISTINCTIVE_VOCABULARY)
            for name_b in names[i + 1:]:
                vocab_b = set(v.lower() for v in THEORISTS[name_b].DISTINCTIVE_VOCABULARY)
                overlap = vocab_a & vocab_b
                smaller = min(len(vocab_a), len(vocab_b))
                ratio = len(overlap) / smaller if smaller > 0 else 0
                assert ratio <= 0.3, (
                    f"{name_a} and {name_b} share too much vocabulary "
                    f"({len(overlap)}/{smaller}={ratio:.0%}): {overlap}"
                )
