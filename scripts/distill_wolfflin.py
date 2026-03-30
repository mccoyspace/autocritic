#!/usr/bin/env python3
"""
Distill Wölfflin's "Principles of Art History" into a critic card.

This script reads the extracted book text, sends it to Claude with a
carefully constructed prompt, and writes the resulting critic card to
critics/wolfflin.json.

The distillation prompt is grounded in our ground-truth module — it
tells the model what to look for but lets the book's own language
shape the output.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import anthropic

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CORPUS_TEXT = PROJECT_ROOT / "v0" / "corpus" / "raw_text" / "principles_of_art_history_heinrich_wolfflin.txt"
OUTPUT_DIR = PROJECT_ROOT / "critics"


def build_prompt(book_text: str) -> tuple[str, str]:
    """Build the system and user prompts for distillation."""

    system = """\
You are distilling an art-theory book into a machine-usable critic card.

Your job is NOT to summarize the book. Your job is to extract the
evaluative logic — the specific criteria, vocabulary, and diagnostic
questions that a multimodal AI system can later use to critique images
from this theorist's point of view.

Requirements:
1. Use the theorist's OWN vocabulary. Do not modernize or genericize.
2. Every criterion must be defensible from the supplied text.
3. Include direct quotes or close paraphrases as citations.
4. Preserve tensions and ambiguities — do not flatten the theory.
5. State what the critic must NOT do (anti-goals).
6. Criteria must be operational: a later system will use them to assess
   images and provide feedback to an image generator.

Output a single JSON object with this structure:
{
  "critic_id": "wolfflin",
  "theorist": "Heinrich Wölfflin",
  "book": "Principles of Art History",
  "thesis": "<one paragraph: what is the core evaluative logic of this book?>",
  "criteria": [
    {
      "criterion_id": "<short snake_case id>",
      "label": "<human-readable name>",
      "pole_a": "<name of one end of the spectrum>",
      "pole_b": "<name of the other end>",
      "definition": "<what does this criterion assess, in the theorist's terms?>",
      "diagnostic_questions": ["<questions to ask when looking at an image>"],
      "indicators": {
        "pole_a": ["<what visual properties indicate this pole?>"],
        "pole_b": ["<what visual properties indicate this pole?>"]
      },
      "feedback_directions": {
        "toward_a": ["<what changes would move the image toward pole A?>"],
        "toward_b": ["<what changes would move the image toward pole B?>"]
      },
      "common_misreadings": ["<ways this criterion is often misapplied>"]
    }
  ],
  "anti_goals": ["<things this critic must never do>"],
  "tensions": [
    {
      "label": "<name of the tension>",
      "description": "<how does this tension manifest in the theory?>"
    }
  ],
  "citations": [
    {
      "claim": "<what claim is being supported>",
      "quote_or_paraphrase": "<the actual text from the book>",
      "location": "<chapter or section reference>"
    }
  ],
  "confidence_notes": ["<where is the theory hard to operationalize?>"]
}

Return ONLY the JSON object. No markdown fences, no commentary."""

    # We need to be strategic about what text to send. The full book is ~580KB.
    # Send the Introduction (theoretical framework) and the "General Observations"
    # sections of each chapter, which contain the definitions.
    # We'll include a generous amount — Claude can handle long context.

    # Take first 80K chars which covers Introduction + most of the theoretical content
    text_sample = book_text[:80000]

    user = f"""\
Below is the text of Heinrich Wölfflin's "Principles of Art History" (1915).

Wölfflin's core framework consists of five opposed stylistic categories,
each a spectrum between two poles:
1. Linear vs. Painterly
2. Plane vs. Recession
3. Closed Form vs. Open Form
4. Multiplicity vs. Unity
5. Clearness vs. Unclearness (Absolute Clarity vs. Relative Clarity)

IMPORTANT CONSTRAINTS for your distillation:
- Neither pole is superior. Wölfflin is explicit about this: "The linear
  style developed values which the painterly style no longer possessed and
  no longer wanted to possess. They are two conceptions of the world."
- The categories are INDEPENDENT. An image can be linear but recessional.
- These describe VISUAL ORGANIZATION, not subject matter.
- Use Wölfflin's own words wherever possible. Key vocabulary includes:
  linear, painterly (malerisch), tactile, visual, plane, recession,
  closed form, open form, tectonic, atectonic, multiplicity, unity,
  clearness, unclearness, silhouette, contour.

Extract all five criteria with their full operational detail. Include
citations from the text for key definitions.

---BEGIN BOOK TEXT---
{text_sample}
---END BOOK TEXT---"""

    return system, user


def main() -> int:
    if not CORPUS_TEXT.exists():
        print(f"error: corpus text not found at {CORPUS_TEXT}", file=sys.stderr)
        return 1

    book_text = CORPUS_TEXT.read_text(encoding="utf-8", errors="replace")
    system, user = build_prompt(book_text)

    print(f"Sending {len(user)} chars to Claude...")
    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8192,
        temperature=0.0,
        system=system,
        messages=[{"role": "user", "content": user}],
    )

    raw = response.content[0].text
    print(f"Got {len(raw)} chars back")

    # Parse and validate JSON
    try:
        card = json.loads(raw)
    except json.JSONDecodeError:
        # Try stripping markdown fences
        import re
        match = re.search(r"```(?:json)?\s*\n(.*?)\n```", raw, re.DOTALL)
        if match:
            card = json.loads(match.group(1))
        else:
            print(f"error: could not parse response as JSON", file=sys.stderr)
            print(raw[:500], file=sys.stderr)
            return 1

    # Write output
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / "wolfflin.json"
    output_path.write_text(json.dumps(card, indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote {output_path}")

    # Quick sanity checks
    criteria = card.get("criteria", [])
    print(f"  Criteria: {len(criteria)}")
    for c in criteria:
        print(f"    - {c.get('label', '?')}")
    print(f"  Anti-goals: {len(card.get('anti_goals', []))}")
    print(f"  Citations: {len(card.get('citations', []))}")
    print(f"  Tensions: {len(card.get('tensions', []))}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
