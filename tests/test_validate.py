"""Tests for critic card validation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from autocritic.validate import validate_card

CRITICS_DIR = Path(__file__).parent.parent / "critics"


class TestValidateExistingCards:
    """All bundled cards should pass validation."""

    def test_all_bundled_cards_pass(self):
        for card_path in sorted(CRITICS_DIR.glob("*.json")):
            passed, messages = validate_card(card_path)
            assert passed, f"{card_path.name} failed: {messages}"


class TestValidateMissingIdField:
    """Cards without ID fields should fail runtime validation."""

    def test_item_without_id_field_fails(self, tmp_path):
        """A card whose items lack a recognized ID field should be flagged."""
        card = {
            "critic_id": "test_no_id",
            "theorist": "Test Theorist",
            "book": "Test Book Title Here",
            "thesis": "This is a test thesis that meets the minimum length requirement for validation.",
            "anti_goals": ["Do not do this"],
            "tensions": [{"label": "T1", "description": "A tension"}],
            "criteria": [
                {
                    # No criterion_id or any other recognized ID field
                    "label": "Test Criterion",
                    "definition": "A test definition that meets the minimum length for schema validation.",
                    "diagnostic_questions": ["Is this a test?"],
                    "indicators": {"strong": ["visible"], "weak": ["not visible"]},
                }
            ],
        }
        card_path = tmp_path / "test_no_id.json"
        card_path.write_text(json.dumps(card))

        passed, messages = validate_card(card_path)
        assert not passed, "Card without ID field should fail validation"
        assert any("missing ID field" in m for m in messages), f"Expected ID field error, got: {messages}"

    def test_item_with_id_field_passes(self, tmp_path):
        """A card with proper ID fields should pass."""
        card = {
            "critic_id": "test_with_id",
            "theorist": "Test Theorist",
            "book": "Test Book Title Here",
            "thesis": "This is a test thesis that meets the minimum length requirement for validation.",
            "anti_goals": ["Do not do this"],
            "tensions": [{"label": "T1", "description": "A tension"}],
            "criteria": [
                {
                    "criterion_id": "test_axis",
                    "label": "Test Criterion",
                    "definition": "A test definition that meets the minimum length for schema validation.",
                    "diagnostic_questions": ["Is this a test?"],
                    "indicators": {"strong": ["visible"], "weak": ["not visible"]},
                }
            ],
        }
        card_path = tmp_path / "test_with_id.json"
        card_path.write_text(json.dumps(card))

        passed, messages = validate_card(card_path)
        assert passed, f"Card with ID field should pass: {messages}"
