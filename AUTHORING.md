# Authoring Critic Cards

This guide explains how to create a new critic card for autocritic — a JSON file that encodes an art theorist's evaluative framework so an LLM can use it to critique images.

## What is a critic card?

A critic card is not a summary of a book. It is a distillation of the book's **evaluative logic** — the specific criteria, vocabulary, and diagnostic questions that tell a multimodal LLM how to see from that theorist's perspective.

A good critic card:
- Uses the theorist's **own vocabulary**, not modernized or genericized language
- Contains only claims **defensible from the source text**
- Preserves **tensions and ambiguities** in the theory
- States what the critic must **never do** (anti-goals)
- Makes criteria **operational**: an LLM must be able to use them to assess images

## Two paths to a critic card

### Path 1: LLM-assisted distillation (recommended)

Use an LLM to read the source text and extract the evaluative framework. See `scripts/distill_wolfflin.py` for a complete example.

The workflow:
1. Obtain the source text in a readable format (plain text, PDF)
2. Write a distillation prompt that includes:
   - The schema constraints (what fields the output must have)
   - Domain-specific guidance (what the theorist's framework looks like)
   - Constraints on vocabulary and citation
3. Send the text + prompt to a long-context LLM (Claude, GPT-4, etc.)
4. Parse and validate the output JSON
5. Save to `critics/<theorist_id>.json`

The distillation prompt should tell the LLM:
- Use the theorist's OWN vocabulary
- Every criterion must be defensible from the text
- Include direct quotes or close paraphrases as citations
- Preserve tensions — do not flatten the theory
- Criteria must be operational for image assessment

### Path 2: Manual authoring

1. Copy `schemas/template_card.json` to `critics/<your_id>.json`
2. Read the template's `_comment` and `_note` fields for guidance
3. Fill in each field based on your reading of the source text
4. Delete all `_comment` and `_note` fields
5. Validate: `python3 -m autocritic validate critics/your_card.json`

## Choosing your items key

The main evaluative items go in an array under one of these keys:

| Key | Use when... | Example |
|-----|-------------|---------|
| `criteria` | The theory defines bipolar axes/spectra | Wölfflin (linear↔painterly) |
| `elements` | The theory builds from basic visual elements | Kandinsky (point, line, plane) |
| `core_concepts` | The theory is organized around central concepts | Arnheim (balance, simplicity, dynamics) |
| `principles` | The theory prescribes compositional principles | Dow (opposition, transition, subordination) |
| `impulses` | The theory identifies psychological drives | Worringer (abstraction, empathy) |

You can also register a new items key by adding it to `_ITEMS_KEYS` and `_ID_FIELDS` in `src/autocritic/critic.py`.

## Card structure

### Required top-level fields

```json
{
  "critic_id": "snake_case_id",
  "theorist": "Full Name",
  "book": "Book Title",
  "thesis": "One paragraph: the core evaluative logic...",
  "<items_key>": [ ... ],
  "anti_goals": [ "Things this critic must never do" ],
  "tensions": [ { "label": "...", "description": "..." } ]
}
```

### Optional top-level fields

```json
{
  "citations": [ { "claim": "...", "quote_or_paraphrase": "...", "location": "..." } ],
  "confidence_notes": [ "Where the theory is hard to operationalize" ]
}
```

### Item structure

Each item in the items array must have:

```json
{
  "<id_field>": "snake_case_id",
  "label": "Human-Readable Name",
  "definition": "What this item assesses, in the theorist's terms",
  "diagnostic_questions": [ "Questions to ask when evaluating..." ],
  "indicators": { ... },
  "feedback_directions": { ... },
  "common_misreadings": [ "How this is often misapplied" ]
}
```

The `<id_field>` name should match the items key:
- `criteria` → `criterion_id`
- `core_concepts` → `concept_id`
- `elements` → `element_id`
- `impulses` → `impulse_id`
- `principles` → `principle_id`

### Bipolar vs. unipolar indicators

**Bipolar** (for criteria with two poles, neither superior):
```json
"indicators": {
  "pole_a": [ "Visual evidence of pole A" ],
  "pole_b": [ "Visual evidence of pole B" ]
},
"feedback_directions": {
  "toward_a": [ "Changes that would move toward pole A" ],
  "toward_b": [ "Changes that would move toward pole B" ]
}
```

Also add `"pole_a": "name"` and `"pole_b": "name"` fields to the item.

Bipolar items are scored on a **-1 to +1** scale. The composite score uses `abs(score)` — commitment to either pole is valued.

**Unipolar** (for concepts with strong/weak presence):
```json
"indicators": {
  "strong_<concept>": [ "Evidence of strong presence" ],
  "weak_<concept>": [ "Evidence of weak presence" ]
},
"feedback_directions": {
  "strengthen": [ "Changes to strengthen this concept" ],
  "reduce": [ "When to pull back" ]
}
```

Unipolar items are scored on a **0 to 1** scale.

## Validation

Validate your card before use:

```bash
python3 -m autocritic validate critics/your_card.json
```

This checks:
1. **JSON Schema** compliance (field types, required fields, structure)
2. **Runtime loading** (the card loads correctly into the critic runtime)
3. **ID consistency** (critic_id matches the filename)
4. **Item completeness** (each item has label, definition, diagnostic questions, indicators)

## Testing

The existing critic cards each have a test file in `tests/test_<critic_id>_card.py`. To create one for your card:

```python
"""Tests for the <theorist> critic card."""
import json
from pathlib import Path
import pytest

CARD_PATH = Path("critics/<your_id>.json")

@pytest.fixture
def card():
    return json.loads(CARD_PATH.read_text())

def test_loads(card):
    from autocritic.critic import load_critic
    critic = load_critic(CARD_PATH)
    assert critic.critic_id == "<your_id>"

def test_required_fields(card):
    assert "critic_id" in card
    assert "theorist" in card
    assert "book" in card
    assert "thesis" in card
    assert "anti_goals" in card
    assert "tensions" in card

def test_items_present(card):
    # Adjust the key to match your card
    assert "<items_key>" in card
    items = card["<items_key>"]
    assert len(items) >= 1
    for item in items:
        assert "label" in item
        assert "definition" in item
        assert "diagnostic_questions" in item
```

## Design principles

These principles guided the creation of the included 10 critic cards:

1. **Fidelity to source**: The card must be defensible from the book. If you can't cite it, don't include it.

2. **Operational vocabulary**: Every term must be usable by an LLM evaluating an image. Abstract concepts need concrete indicators.

3. **Preserved tensions**: Real art theory is full of contradictions and edge cases. Document them in `tensions` and `confidence_notes` — don't smooth them out.

4. **Anti-goals matter**: What the critic must NOT do is as important as what it must do. Wölfflin's anti-goals include "never treat either pole as superior." Without this constraint, the LLM will default to praising one mode over the other.

5. **Diagnostic questions drive evaluation**: The `diagnostic_questions` field is what the LLM actually uses to look at the image. Make them specific and observable.

6. **Indicators must be visual**: "The artist intended tension" is not an indicator. "Diagonal lines converging toward the upper right" is.
