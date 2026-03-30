"""
Ground truth for Rudolf Arnheim's "Art and Visual Perception" (1954/1974).

Arnheim applies Gestalt psychology to visual art. His core thesis: perception
is not passive recording but active organization. The eye doesn't just receive —
it structures. Every visual experience involves forces, tensions, balance,
and simplification happening at the level of perception itself.

Key challenge: Arnheim's framework is exceptionally broad. It covers
balance, shape, form, space, light, color, movement, dynamics, and expression.
A naive distillation risks producing generic art criticism because Arnheim's
categories overlap heavily with standard design vocabulary.

The distinctive Arnheim move: treating visual properties as PERCEPTUAL FORCES,
not just formal attributes. Balance isn't "things are even" — it's "forces
in the visual field reach equilibrium." Shape isn't "outline" — it's "the
simplest structure that captures the stimulus." This force-language is what
separates Arnheim from generic design talk.
"""

# Arnheim's key perceptual principles (not just chapter topics).
PRINCIPLES = {
    "balance": {
        "definition": (
            "Every visual pattern has a structural skeleton of forces. "
            "Balance is the state in which these forces reach equilibrium. "
            "An unbalanced composition creates perceptual stress — the eye "
            "seeks resolution."
        ),
        "key_concepts": [
            "Weight: visual elements have 'weight' based on size, color, "
            "isolation, intrinsic interest, and position",
            "Direction: elements create directional vectors based on shape, "
            "position relative to frame, and implied movement",
            "The 'hidden structure' of any format (the center, axes, and "
            "diagonals create a force field before any element is placed)",
            "Top vs. bottom asymmetry: top is perceptually lighter, bottom heavier",
            "Left vs. right asymmetry: we scan left to right, creating "
            "different perceptual weight",
        ],
        "what_to_look_for": [
            "Where is the visual center of gravity?",
            "Do the weights and directions reach equilibrium or create unresolved stress?",
            "Is imbalance intentional (expressive) or accidental?",
        ],
    },
    "simplicity": {
        "definition": (
            "Perception tends toward the simplest structure that adequately "
            "captures the stimulus. This is the Gestalt law of Prägnanz. "
            "Visual tension arises when the stimulus resists simplification."
        ),
        "key_concepts": [
            "The structural skeleton: the simplest framework underlying a form",
            "Leveling (reducing tension, increasing symmetry) vs. "
            "sharpening (increasing distinction, exaggerating difference)",
            "Good continuation: the eye extends lines and curves along their "
            "established direction",
            "Subdivision: how a whole breaks into parts, and how parts "
            "regroup into wholes",
        ],
    },
    "dynamics": {
        "definition": (
            "Every visual pattern contains directed tensions — forces that "
            "the eye perceives as movement, pull, push, expansion, or "
            "compression, even in completely static images. Dynamics is not "
            "depicted movement but perceived force."
        ),
        "key_concepts": [
            "Tension is created by deviation from the simplest structure "
            "(a tilted rectangle is 'tense' because it deviates from vertical)",
            "Obliqueness is inherently dynamic — it implies movement toward "
            "or away from the horizontal/vertical",
            "Deformation creates tension: a compressed circle 'wants to' "
            "return to circularity",
            "The dynamic character of a composition is its most expressive "
            "property — it IS the expression, not a vehicle for it",
        ],
    },
    "expression": {
        "definition": (
            "Expression is not projected onto forms by the viewer — it is "
            "embedded in the structural properties of the percept itself. "
            "A weeping willow looks sad not because we associate it with "
            "sadness but because its structural dynamics (drooping, yielding "
            "to gravity) directly convey that expressive quality."
        ),
        "key_concepts": [
            "Expression is a perceptual property, not an interpretation",
            "The 'physiognomic' character of visual forms: forms have "
            "'faces' — they look aggressive, gentle, tense, relaxed",
            "Expression arises from dynamics: the forces within a form "
            "determine its expressive character",
        ],
    },
}

ESSENTIAL_CLAIMS = [
    "Perception is active organization, not passive reception. The eye "
    "structures what it sees according to Gestalt laws.",
    "Visual properties are perceptual forces, not just formal attributes. "
    "Balance, tension, and dynamics are felt, not just measured.",
    "The tendency toward simplest structure (Prägnanz) governs all perception. "
    "Complexity is perceived as deviation from simplicity and creates tension.",
    "Expression is not separate from form — it IS form. The structural "
    "dynamics of a visual pattern are directly expressive.",
    "Every visual field has an inherent structure (center, axes, diagonals) "
    "that exists before any element is placed, and interacts with everything "
    "that IS placed.",
    "Art makes visible the forces that underlie appearances. A good portrait "
    "doesn't copy a face — it captures the dynamic forces that animate it.",
]

ANTI_GOALS = [
    "Must not flatten Arnheim into generic design principles (balance, "
    "emphasis, contrast, etc.) — the force/tension language is essential",
    "Must not describe visual properties as static attributes — always as "
    "forces, tensions, or dynamic relations",
    "Must not separate 'expression' from 'form' — for Arnheim they are one",
    "Must not treat balance as 'symmetry' — balance is equilibrium of "
    "forces, which asymmetric compositions can achieve",
    "Must not ignore the perceptual basis — criteria must refer to what "
    "the eye does, not just what the image contains",
]

DISTINCTIVE_VOCABULARY = [
    "perceptual forces", "visual weight", "visual direction",
    "structural skeleton", "simplest structure",
    "tension", "dynamics", "Prägnanz",
    "leveling", "sharpening",
    "good continuation",
    "equilibrium", "center of gravity",
    "physiognomic", "expressive properties",
    "obliqueness",
]

GOOD_CRITIQUE_EXAMPLE = (
    "The visual center of gravity sits slightly above and left of geometric "
    "center, creating a mild leftward pull that the heavy dark mass at "
    "lower-right counterbalances — equilibrium is achieved asymmetrically. "
    "The dominant dynamic force is the oblique thrust of the central form, "
    "which deviates sharply from the vertical axis and generates strong "
    "tension: the eye perceives it as 'falling' or 'leaning,' demanding "
    "resolution. The structural skeleton of the composition reduces to a "
    "triangle resting on one vertex — inherently unstable, which gives the "
    "whole image an expressive quality of precariousness. Simplification is "
    "mostly achieved: forms reduce cleanly to their essential structure, "
    "though the cluster at upper-right resists grouping and fragments the eye."
)

BAD_CRITIQUE_EXAMPLE = (
    "The composition is well-balanced with good use of visual weight. The "
    "forms have dynamic qualities and the overall expression is effective. "
    "There is a nice interplay between the different elements."
)
