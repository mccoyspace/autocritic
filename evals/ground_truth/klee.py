"""
Ground truth for Paul Klee's "Pedagogical Sketchbook" (1925).

Klee's framework is about genesis — the process by which forms come into
being. A line is not a thing but an act: a point shifting its position
forward. Forms are not static results but records of movement, energy,
and growth. The book progresses from line to structure to balance to
dynamics to chromatic energy.

Key challenge: Klee thinks in terms of process and organism, not formal
properties. A naive distillation risks producing static formal categories.
The distinctive Klee move: every form is a trace of its own creation —
the critic must read forms as records of movement and energy, not as
fixed geometric shapes.
"""

CORE_CONCEPTS = {
    "line_as_movement": {
        "definition": (
            "An active line on a walk, moving freely, without goal. A walk "
            "for a walk's sake. The mobility agent is a point, shifting its "
            "position forward. The line is not a boundary or outline but a "
            "record of movement — it carries the energy of its own genesis."
        ),
        "line_types": [
            "Active line: a point in motion, the agent of movement",
            "Medial line: both point progression and planar effect",
            "Passive line: the result of an activation of planes",
        ],
    },
    "structural_rhythm": {
        "definition": (
            "Repetition of units creates structural rhythm — purely "
            "repetitive and therefore structural. Any number of parts can "
            "be added or taken away without changing rhythmic character. "
            "Individual articulation resists reduction and demands "
            "proportions like the Golden Section."
        ),
    },
    "non_symmetrical_balance": {
        "definition": (
            "Balance achieved not through mirror symmetry but through "
            "counterweights — metric balance, weight balance, character "
            "balance. Building a tower: each stone creates disturbance "
            "corrected by the next. The tightrope walker is the scale."
        ),
    },
    "gravitational_dynamics": {
        "definition": (
            "There are regions with different laws and new symbols, "
            "signifying freer movement and dynamic position. Earth binds "
            "with gravity; water and atmosphere are transitional regions "
            "where movement becomes freer. The arrow is the father of "
            "thought: how do I expand my reach?"
        ),
    },
    "kinetic_and_chromatic_energy": {
        "definition": (
            "The pendulum creates equilibration of movement. The spinning "
            "top replaces material support with gyration. The spiral "
            "transforms the circle through changing radius. Chromatic "
            "energy operates through arrows of color — heating and "
            "cooling that can become one when direction is transcended."
        ),
    },
}

ESSENTIAL_CLAIMS = [
    "The line is a record of movement, not a static boundary. An active "
    "line is a point shifting its position forward — a walk for a walk's sake.",
    "Forms have three conjugations: active (I fell the tree), medial (the "
    "tree falls), passive (the tree lies felled). Every form participates "
    "in this grammar of energy.",
    "Structural rhythm is purely repetitive — individual articulation "
    "resists reduction and demands proportion (Golden Section).",
    "Balance is non-symmetrical: achieved through counterweights and "
    "correction, not mirror symmetry. The tightrope walker is the scale.",
    "The contrast between man's ideological capacity to move through "
    "material and metaphysical spaces and his physical limitations is the "
    "origin of all human tragedy. Half winged — half imprisoned, this is man.",
    "The work grows stone upon stone (additive) or is hewn chip from chip "
    "(subtractive). The work as human action is productive as well as "
    "receptive. It is continuity.",
]

ANTI_GOALS = [
    "Must not treat forms as static geometric shapes — every form is a "
    "record of movement and energy, a trace of its own genesis",
    "Must not ignore the three conjugations (active, medial, passive) — "
    "they reveal the energy grammar of the composition",
    "Must not reduce balance to symmetry — Klee's balance is achieved "
    "through counterweights, correction, and dynamic equilibrium",
    "Must not separate form from process — the line is an act, not a thing",
    "Must not ignore gravitational and kinetic dynamics — forms exist in "
    "relation to gravity, momentum, and energy",
]

DISTINCTIVE_VOCABULARY = [
    "active line", "medial line", "passive line",
    "conjugation", "genesis",
    "structural rhythm", "divisional articulation",
    "individual articulation", "Golden Section",
    "non-symmetrical balance", "tightrope walker",
    "gravitational curve", "kinetic energy",
    "chromatic energy", "arrow",
    "pendulum", "spinning top", "spiral",
]

GOOD_CRITIQUE_EXAMPLE = (
    "The dominant line reads as active — a point in continuous forward "
    "motion, carrying the energy of its genesis visibly in its varying "
    "weight and direction. The secondary forms are passive: boundaries "
    "created by the activation of planes, their linearity replaced by "
    "planarity once completed. The structural rhythm of the repeated "
    "verticals is purely repetitive, but the irregular spacing of the "
    "horizontal accents introduces individual articulation that resists "
    "reduction. Balance is non-symmetrical — the heavy mass at lower-left "
    "is counterweighted by the kinetic energy of the ascending diagonal, "
    "creating a tightrope-walker equilibrium. The overall dynamic is one "
    "of gravitational pull countered by aspiration — half imprisoned, "
    "half winged."
)

BAD_CRITIQUE_EXAMPLE = (
    "The composition uses a variety of lines and shapes. The balance is "
    "good with elements distributed across the canvas. The movement "
    "creates visual interest and guides the eye through the piece."
)
