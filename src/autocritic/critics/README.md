# Critic Cards

Each JSON file in this directory encodes one art theorist's evaluative framework for machine use. These cards are loaded by the autocritic runtime and used to instruct multimodal LLMs on how to critique images from a specific theoretical perspective.

## Included cards

| File | Theorist | Source text | Items |
|------|----------|-------------|-------|
| `albers.json` | Josef Albers | *Interaction of Color* (1963) | 4 core concepts |
| `arnheim.json` | Rudolf Arnheim | *Art and Visual Perception* (1954) | 4 principles |
| `dow.json` | Arthur Wesley Dow | *Composition* (1899) | 3 elements + 5 principles |
| `gombrich.json` | Ernst Gombrich | *The Sense of Order* (1979) | 4 core concepts |
| `hildebrand.json` | Adolf Hildebrand | *The Problem of Form* (1893) | 5 core concepts |
| `kandinsky.json` | Wassily Kandinsky | *Point and Line to Plane* (1926) | 3 elements + 4 principles |
| `klee.json` | Paul Klee | *Pedagogical Sketchbook* (1925) | 5 core concepts |
| `ruskin.json` | John Ruskin | *The Elements of Drawing* (1857) | 5 core concepts |
| `wolfflin.json` | Heinrich Wölfflin | *Principles of Art History* (1915) | 5 criteria |
| `worringer.json` | Wilhelm Worringer | *Abstraction and Empathy* (1908) | 2 impulses + 3 dimensions |

## Card structure

Every card has:

- **`critic_id`** — unique snake_case identifier matching the filename
- **`theorist`** — full name of the theorist
- **`book`** — title of the source text
- **`thesis`** — one paragraph summary of the evaluative logic
- **items array** — the evaluative criteria/concepts/elements (key varies by card)
- **`anti_goals`** — what this critic must never do
- **`tensions`** — internal contradictions or edge cases in the theory
- **`citations`** — quoted or paraphrased evidence from the source text
- **`confidence_notes`** (optional) — where the distillation is uncertain

Each item in the items array has:

- **`label`** — human-readable name
- **`definition`** — what this item assesses, in the theorist's terms
- **`diagnostic_questions`** — questions the LLM asks when looking at an image
- **`indicators`** — observable visual evidence (bipolar: `pole_a`/`pole_b`; unipolar: `strong_X`/`weak_X`)
- **`feedback_directions`** — actionable changes an image generator could make
- **`common_misreadings`** — how this item is often misunderstood

## Bipolar vs. unipolar

Cards fall into two scoring modes, auto-detected by the runtime:

**Bipolar** (Wölfflin, Kandinsky, Worringer): Items have `pole_a`/`pole_b` indicators. Scored -1 to +1. Neither pole is superior — both are valid modes. Composite score uses `abs(score)` to measure commitment to either pole.

**Unipolar** (all others): Items have `strong_X`/`weak_X` indicators. Scored 0 to 1. Higher means stronger presence of the concept.

## Validation

```bash
python3 -m autocritic validate critics/*.json
```

## Creating new cards

See [AUTHORING.md](../AUTHORING.md) for the full guide, and [schemas/](../schemas/) for the JSON schema and template.
