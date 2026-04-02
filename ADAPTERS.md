# Writing a Generator Adapter

A generator adapter connects autocritic's improvement loop to your generative system. The adapter tells autocritic what parameters your system has, what they mean aesthetically, and how to acquire an image from a set of parameter values.

The loop controller (`loop.py`) is generator-agnostic. It only needs two things from an adapter:

1. A **`ParamSpace`** describing your tunable parameters
2. An **`acquire_image`** function that turns parameters into a PNG

Everything else — critiquing, scoring, translating critiques into parameter changes — is handled by the shared autocritic runtime.

## The parameter model

The parameter model is the core of the adapter contract. It serves two audiences:

- **The loop controller** uses it to clamp values, apply damping, and provide defaults.
- **The LLM translator** reads parameter descriptions to reason about which parameters to change in response to a critique.

### ParamSpec

Each parameter is defined as a `ParamSpec`:

```python
from autocritic.translator import ParamSpec

ParamSpec(
    name="layout_spread",       # identifier (matches keys in param dicts)
    type="float",               # "int", "float", or "enum"
    range=(0.1, 5.0),           # (min, max) for numeric; tuple of valid values for enum
    default=1.15,               # starting value
    description="Controls spacing between nodes in the force-directed layout. "
                "Higher = more spread out, airier composition with more negative space. "
                "Lower = tighter clustering, denser visual mass.",
)
```

Supported types:

| Type | `range` format | Damping | Example |
|------|---------------|---------|---------|
| `int` | `(min, max)` | Interpolated, then rounded | `(1, 300)` |
| `float` | `(min, max)` | Interpolated | `(0.01, 20.0)` |
| `enum` | `(val1, val2, ...)` | Set directly (no interpolation) | `("random", "hub_first")` |

### ParamSpace

A `ParamSpace` groups your specs and provides three utility methods:

```python
from autocritic.translator import ParamSpace

MY_PARAM_SPACE = ParamSpace(specs=[...])

MY_PARAM_SPACE.defaults()    # -> {"param": default, ...}
MY_PARAM_SPACE.clamp(params) # -> params with values forced into valid ranges
MY_PARAM_SPACE.describe()    # -> formatted markdown string for LLM consumption
```

`describe()` produces the text that the LLM translator reads when deciding what to change. This is why good descriptions matter — see below.

## Writing good parameter descriptions

The `description` field on each `ParamSpec` is the most important part of your adapter. The LLM translator has no hardcoded knowledge of your system. It reads the critique (e.g. "the composition lacks negative space and feels claustrophobic") and then reads your parameter descriptions to figure out which knobs to turn. If your descriptions don't bridge the gap between aesthetic language and parameter semantics, the translator can't do its job.

### Guidelines

**Describe visual effect, not implementation.** The translator doesn't care that `layout_iterations` controls a spring-relaxation algorithm. It cares that more iterations produce "smoother, more settled node arrangement with clearer spatial structure" and fewer produce "more chaotic, compressed, organic-feeling positioning."

**Describe both directions.** For numeric parameters, explain what happens at the low end and the high end. The translator needs to know which direction to push.

```python
# Good: both directions described
"Line thickness in millimeters. Thicker = bolder, more visual mass, more painterly. "
"Thinner = more delicate, more linear, finer detail."

# Bad: only one direction
"Controls line thickness."
```

**Use the critic's vocabulary.** If you're using the Wolfflin critic, and its axes include "linear vs. painterly," a description that uses the words "linear" and "painterly" will produce better translations. Look at the critic cards you plan to use and echo their language where it applies naturally.

**Note dependencies between parameters.** If a parameter only has effect under certain conditions, say so:

```python
"When draw_mode=short, what percentile of edge lengths to keep. "
"Lower = sparser, showing only the tightest local connections. "
"Higher = more edges visible. Only active when draw_mode=short."
```

**Keep it concise but complete.** Two to four sentences is typical. The full parameter space description is included in the translator prompt, so extremely verbose descriptions eat into the context budget.

## The acquire_image interface

Your adapter must provide a function with this signature:

```python
def acquire_image(
    params: dict[str, Any],
    output_path: Path,
    **kwargs,
) -> Path:
```

- `params`: a dict of parameter values (keys match your `ParamSpec.name` fields)
- `output_path`: where to save the resulting PNG (the loop creates the parent directory)
- Returns the path to the saved image (usually just `output_path`)

The loop calls this function once per iteration. What happens inside is entirely up to you — run a local process, call an HTTP API, invoke a shader, render a 3D scene. The only requirement is that a PNG ends up at `output_path`.

### Example: the rewriter adapter

The rewriter adapter (`adapters/rewriter.py`) talks to a FastAPI server over HTTP:

```
acquire_image(params, output_path)
  └─ export_frame(params)          # POST /api/export → SVG path
       └─ fetch_file(svg_path)     # GET the SVG bytes
            └─ svg_to_png(bytes)   # cairosvg conversion
                 └─ write PNG to output_path
```

This is one pattern. A simpler adapter might just call a Python function directly:

```python
def acquire_image(params, output_path, **kwargs):
    my_generator.render(output_path, **params)
    return output_path
```

## Plugging into the loop

With a `ParamSpace` and an `acquire_image` function, you can run the improvement loop:

```python
from autocritic.loop import LoopConfig, run_loop
from my_adapter import MY_PARAM_SPACE, acquire_image

config = LoopConfig(
    critic_card_path=Path("critics/wolfflin.json"),
    model="openai:gpt-5.4-mini",
    max_iterations=5,
    generator_name="my_generator",
)

result = run_loop(
    config,
    param_space=MY_PARAM_SPACE,
    acquire_image_fn=lambda params, path: acquire_image(params, path),
)
```

The loop handles everything else: loading the critic card, calling the LLM for scoring and translation, applying deltas with damping, accept/reject logic, saving artifacts.

## How delta application works

When the translator says "set `layout_spread` to 3.0" and the current value is 1.0, the loop doesn't jump straight to 3.0. It applies **damping**:

```
new = current + damping * (target - current)
```

With the default damping of 0.7: `new = 1.0 + 0.7 * (3.0 - 1.0) = 2.4`

This prevents wild oscillation. If an iteration is rejected (score didn't improve), the loop halves the damping and retries, producing an even more conservative step.

Enum parameters are set directly — there's no meaningful way to interpolate between discrete values.

After applying deltas, `param_space.clamp()` enforces all ranges, so the generator always receives valid values.

## Adapter checklist

- [ ] Define a `ParamSpace` with a `ParamSpec` for every tunable parameter
- [ ] Write descriptions that bridge aesthetic language and parameter semantics
- [ ] Implement `acquire_image(params, output_path) -> Path` that saves a PNG
- [ ] Add any required dependencies as an optional dep group in `pyproject.toml`
- [ ] Place adapter in `src/autocritic/adapters/`
- [ ] Test that `param_space.defaults()` produces a valid generation
- [ ] Test that `param_space.clamp()` handles edge cases (out-of-range, wrong type)

## Reference

- Working adapter: `src/autocritic/adapters/rewriter.py`
- Parameter model: `src/autocritic/translator.py` (`ParamSpace`, `ParamSpec`, `apply_deltas`)
- Loop controller: `src/autocritic/loop.py` (`LoopConfig`, `run_loop`)
- Critic cards: `critics/` (look at these to understand what language the translator will be working with)
