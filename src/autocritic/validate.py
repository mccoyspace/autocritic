"""
Validate critic card JSON files against the schema and runtime loader.

Usage:
    python3 -m autocritic validate critics/my_card.json
    python3 -m autocritic validate critics/*.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Schema bundled with the package
SCHEMA_PATH = Path(__file__).resolve().parent / "schemas" / "critic_card.schema.json"


def _validate_with_jsonschema(card: dict, card_path: Path) -> list[str]:
    """Validate against JSON Schema. Returns list of error messages."""
    try:
        import jsonschema
    except ImportError:
        return ["jsonschema not installed — skipping schema validation. Install with: pip install 'autocritic[dev]'"]

    if not SCHEMA_PATH.exists():
        return [f"Schema file not found at {SCHEMA_PATH}"]

    schema = json.loads(SCHEMA_PATH.read_text())
    errors = []
    validator = jsonschema.Draft202012Validator(schema)
    for error in sorted(validator.iter_errors(card), key=lambda e: list(e.path)):
        path = ".".join(str(p) for p in error.path) or "(root)"
        errors.append(f"  {path}: {error.message}")
    return errors


def _validate_runtime(card_path: Path) -> list[str]:
    """Try loading the card with the runtime loader. Returns list of error messages."""
    errors = []
    try:
        from autocritic.critic import load_critic
        critic = load_critic(card_path)

        # Check that critic_id matches filename
        expected_id = card_path.stem
        if critic.critic_id != expected_id:
            errors.append(f"  critic_id '{critic.critic_id}' does not match filename '{expected_id}'")

        # Check items aren't empty
        if not critic.items:
            errors.append("  No items found (criteria/core_concepts/elements/impulses/principles)")

        # Check each primary item has required subfields
        for i, item in enumerate(critic.items):
            item_id = item.get(critic.item_id_field, item.get("id", f"item_{i}"))
            if "label" not in item:
                errors.append(f"  {item_id}: missing 'label'")
            if "definition" not in item:
                errors.append(f"  {item_id}: missing 'definition'")
            if "diagnostic_questions" not in item:
                errors.append(f"  {item_id}: missing 'diagnostic_questions' (required for primary items)")
            if "indicators" not in item:
                errors.append(f"  {item_id}: missing 'indicators' (required for primary items)")

        # Check secondary items have at least label + definition
        for sec_key, sec_items in critic.secondary_items.items():
            for i, item in enumerate(sec_items):
                item_id = item.get("label", f"{sec_key}[{i}]")
                if "label" not in item:
                    errors.append(f"  {sec_key}[{i}]: missing 'label'")
                if "definition" not in item:
                    errors.append(f"  {sec_key}[{i}]: missing 'definition'")

    except Exception as e:
        errors.append(f"  Runtime load failed: {e}")
    return errors


def validate_card(card_path: Path) -> tuple[bool, list[str]]:
    """Validate a single critic card. Returns (passed, messages)."""
    messages = []

    # 1. Parse JSON
    try:
        card = json.loads(card_path.read_text())
    except json.JSONDecodeError as e:
        return False, [f"Invalid JSON: {e}"]

    # 2. Schema validation
    schema_errors = _validate_with_jsonschema(card, card_path)
    if schema_errors:
        messages.append("Schema validation:")
        messages.extend(schema_errors)

    # 3. Runtime validation
    runtime_errors = _validate_runtime(card_path)
    if runtime_errors:
        messages.append("Runtime validation:")
        messages.extend(runtime_errors)

    # Determine pass/fail
    has_errors = bool(schema_errors) or bool(runtime_errors)
    # Distinguish warnings (like jsonschema not installed) from real errors
    is_warning_only = (
        len(schema_errors) == 1
        and "not installed" in schema_errors[0]
        and not runtime_errors
    )

    passed = not has_errors or is_warning_only
    return passed, messages


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for validation."""
    if argv is None:
        argv = sys.argv[1:]

    if not argv:
        print("Usage: python3 -m autocritic validate <card.json> [card2.json ...]")
        print("       python3 -m autocritic validate critics/*.json")
        return 1

    paths = [Path(a) for a in argv]
    total = 0
    passed = 0
    failed = 0

    for p in paths:
        if not p.exists():
            print(f"SKIP  {p} (not found)")
            continue
        if not p.suffix == ".json":
            continue

        total += 1
        ok, messages = validate_card(p)
        if ok:
            passed += 1
            status = "OK"
        else:
            failed += 1
            status = "FAIL"

        print(f"{status}  {p.name}")
        for msg in messages:
            print(f"      {msg}")

    print(f"\n{passed}/{total} passed", end="")
    if failed:
        print(f", {failed} failed")
    else:
        print()

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
