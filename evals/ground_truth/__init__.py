"""Registry of ground-truth modules for each theorist."""

from evals.ground_truth import (
    albers,
    arnheim,
    dow,
    gombrich,
    hildebrand,
    kandinsky,
    klee,
    ruskin,
    wolfflin,
    worringer,
)

# Map from short name to ground-truth module.
THEORISTS = {
    "wolfflin": wolfflin,
    "kandinsky": kandinsky,
    "dow": dow,
    "worringer": worringer,
    "arnheim": arnheim,
    "gombrich": gombrich,
    "albers": albers,
    "klee": klee,
    "ruskin": ruskin,
    "hildebrand": hildebrand,
}
