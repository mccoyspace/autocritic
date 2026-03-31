# autocritic

Critic-card-driven image evaluation using art theory and multimodal LLMs.

Load a **critic card** distilled from an art theory book. The critic evaluates images through that theorist's lens, producing structured qualitative feedback with numeric scores. An optional **improvement loop** feeds critiques back into a generative system, steering parameter changes through LLM-driven translation — no hardcoded mapping tables.

## How it works

```
                    ┌──────────────┐
                    │  Critic Card │  (JSON: Wölfflin, Kandinsky, Arnheim, ...)
                    │  ─ thesis    │
                    │  ─ criteria  │
                    │  ─ indicators│
                    └──────┬───────┘
                           │
    ┌─────────┐    ┌───────▼───────┐    ┌──────────────┐
    │  Image  │───▶│  LLM Vision   │───▶│ ScoredCritique│
    └─────────┘    │  (critique)   │    │ ─ axis scores │
                   └───────────────┘    │ ─ directives  │
                                        └───────┬───────┘
                                                │
                              ┌──────────────────▼──────────────────┐
                              │         LLM Translator              │
                              │  critique → parameter deltas        │
                              │  (no hardcoded mapping — LLM reasons│
                              │   about which params to change)     │
                              └──────────────────┬──────────────────┘
                                                 │
                                        ┌────────▼────────┐
                                        │    Generator    │
                                        │ (rewriteDrawer, │
                                        │  morphogenesis, │
                                        │   your system)  │
                                        └─────────────────┘
```

## Installation

```bash
pip install -e ".[dev]"

# For OpenAI models:
pip install -e ".[openai]"

# For Anthropic models:
pip install -e ".[anthropic]"

# For the rewriteDrawer adapter:
pip install -e ".[wolfram]"

# Everything:
pip install -e ".[all-llms,wolfram,dev]"
```

Requires Python 3.11+.

## Quickstart

### Evaluate a single image

```python
from autocritic import load_critic, critique_image

critic = load_critic("critics/wolfflin.json")
result = critique_image(critic, "path/to/image.png")
print(result.summary())
```

### Score an image with numeric axis scores

```python
from autocritic import load_critic, score_critique

critic = load_critic("critics/arnheim.json")
scored = score_critique(critic, "path/to/image.png", model="openai:gpt-5.4-mini")

print(f"Composite: {scored.composite_score:.2f}")
for axis in scored.axis_scores:
    print(f"  {axis.label}: {axis.score:.2f} — {axis.reasoning}")
```

### Critique from the command line

```bash
# Critique any image — no generator needed
python3 -m autocritic critique photo.jpg --critic ruskin --model openai:gpt-5.4-mini

# Try different theoretical lenses on the same image
python3 -m autocritic critique drawing.png --critic kandinsky --model openai:gpt-5.4-mini
python3 -m autocritic critique drawing.png --critic arnheim --model openai:gpt-5.4-mini

# See available critics
python3 -m autocritic list
```

### Run the improvement loop

The improvement loop connects autocritic to a generative system. It generates an image, critiques it, translates the critique into parameter changes, and repeats.

```bash
# Start your generator server first (e.g. rewriteDrawer), then:
python3 -m autocritic run --critic wolfflin --generator wolfram --model openai:gpt-5.4-mini --iterations 5

# Try different critics to get different aesthetic directions
python3 -m autocritic run --critic kandinsky --generator wolfram --model openai:gpt-5.4-mini --iterations 5

# Add an intent to guide the critique
python3 -m autocritic run --critic arnheim --generator wolfram --model openai:gpt-5.4-mini --iterations 5 --intent "organic branching structure"
```

Results are saved to `runs/` with a contact sheet and narrative summary.

### Other commands

```bash
# Validate critic card files
python3 -m autocritic validate critics/*.json

# Generate a contact sheet for an existing run
python3 -m autocritic report runs/wolfram_1774718482/
```

## Available critics

| Card | Theorist | Book | Type |
|------|----------|------|------|
| `albers` | Josef Albers | *Interaction of Color* | 4 core concepts (unipolar) |
| `arnheim` | Rudolf Arnheim | *Art and Visual Perception* | 4 principles (unipolar) |
| `dow` | Arthur Wesley Dow | *Composition* | 3 elements + 5 principles (unipolar) |
| `gombrich` | Ernst Gombrich | *The Sense of Order* | 4 core concepts (unipolar) |
| `hildebrand` | Adolf Hildebrand | *The Problem of Form* | 5 core concepts (unipolar) |
| `kandinsky` | Wassily Kandinsky | *Point and Line to Plane* | 3 elements + 4 principles (bipolar) |
| `klee` | Paul Klee | *Pedagogical Sketchbook* | 5 core concepts (unipolar) |
| `ruskin` | John Ruskin | *The Elements of Drawing* | 5 core concepts (unipolar) |
| `wolfflin` | Heinrich Wölfflin | *Principles of Art History* | 5 criteria (bipolar) |
| `worringer` | Wilhelm Worringer | *Abstraction and Empathy* | 2 impulses + 3 dimensions (bipolar) |

**Bipolar** critics (Wölfflin, Kandinsky, Worringer) score on a -1 to +1 spectrum between two poles — neither pole is superior. **Unipolar** critics score 0 to 1 on presence/strength of each concept.

## Authoring new critics

See [AUTHORING.md](AUTHORING.md) for the full guide to creating your own critic cards, and [schemas/](schemas/) for the JSON schema and template.

Quick overview:
1. Start from `schemas/template_card.json`
2. Fill in the theorist's evaluative framework
3. Validate: `python3 -m autocritic validate critics/your_card.json`

## Architecture

```
src/autocritic/
├── critic.py        # Load critic cards, generate qualitative critiques
├── scoring.py       # Extend critiques with numeric axis scores
├── translator.py    # LLM-driven critique → parameter delta translation
├── loop.py          # Generate → critique → translate → adjust → repeat
├── report.py        # Contact sheets and narrative summaries
├── validate.py      # Critic card validation against schema
├── __main__.py      # CLI entry point
└── adapters/
    └── wolfram.py   # rewriteDrawer HTTP client and parameter space

critics/             # 10 critic cards (JSON)
schemas/             # JSON schema and template for authoring
evals/               # Evaluation harness and ground truth
scripts/             # Distillation scripts (book → critic card)
tests/               # Test suite
```

## Key concepts

- **Critic card**: A JSON file encoding one art theorist's evaluative framework — thesis, criteria, indicators, diagnostic questions, feedback directions, anti-goals. The card tells the LLM *how to see* from that theorist's perspective.

- **ParamSpace**: A generator-agnostic description of tunable parameters. Any generative system that defines a ParamSpace can plug into the improvement loop.

- **LLM-driven translation**: Instead of hardcoded mapping tables from critique terms to parameter names, the LLM reads the critique, looks at the parameter space, and reasons about what to change. This is the core design principle — flexibility over rigidity.

- **Damped deltas**: Parameter changes are applied with damping (`new = current + damping * (target - current)`) to prevent oscillation. Rejected iterations halve the deltas before retrying.

## License

MIT. See [LICENSE](LICENSE).

The critic cards in `critics/` are derived from published art theory texts. The cards contain original analysis and selected citations under fair use. The source texts themselves are not included in this repository.
