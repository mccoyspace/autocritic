"""
Ground truth for Wilhelm Worringer's "Abstraction and Empathy" (1908).

Worringer argues that all art oscillates between two fundamental psychological
impulses: the urge to empathy (Einfühlung) and the urge to abstraction. These
are not style labels but deep psychic orientations toward the external world.

This is a highly philosophically abstract text. It does NOT provide
a checklist of visual criteria. Instead, it provides a diagnostic framework:
given an image, what is its relationship to the visible world, and what
psychological stance does that relationship express?

Key challenge for operationalization: Worringer's theory is about WHY art
looks the way it does, not WHAT it should look like. A Worringer-based critic
must assess the coherence of an image's stance toward representation, not
grade it on formal properties.
"""

# The two fundamental impulses.
IMPULSES = {
    "empathy": {
        "german": "Einfühlung",
        "definition": (
            "The urge to empathy arises from a happy pantheistic relationship "
            "of confidence between man and the phenomena of the external world. "
            "The viewer projects their own vitality into forms, finding pleasure "
            "in organic rhythm, natural proportion, and the sense of living "
            "freely within the form."
        ),
        "art_character": [
            "Naturalistic representation",
            "Organic forms and rhythms",
            "Spatial depth and atmospheric illusionism",
            "The viewer can 'live into' the forms — they feel inhabitable",
            "Confidence in the visible world as a source of beauty",
        ],
        "psychological_basis": (
            "A sense of being at home in the world. The external world is not "
            "threatening but familiar. The viewer's self-activation is in "
            "harmony with what the forms demand."
        ),
    },
    "abstraction": {
        "german": "Abstraktion",
        "definition": (
            "The urge to abstraction is the outcome of a greater inner unrest "
            "inspired in man by the phenomena of the outside world. It seeks "
            "to wrest the object out of the unending flux of being, to purify "
            "it of all dependence on life, to render it necessary and "
            "irrefragible, to approximate it to its absolute value."
        ),
        "art_character": [
            "Geometric regularity and crystalline form",
            "Suppression of depth and space ('space is the major enemy')",
            "Reduction to plane and surface",
            "Repetition and pattern over organic variation",
            "The image seeks permanence, not vitality",
        ],
        "psychological_basis": (
            "An immense spiritual dread of space (Raumscheu). The external "
            "world is threatening and chaotic. Art provides refuge in forms "
            "that are necessary, stable, and stripped of the arbitrary."
        ),
    },
}

# The key diagnostic question a Worringer critic must ask.
CORE_DIAGNOSTIC = (
    "What is this image's relationship to the flux of the visible world? "
    "Does it embrace that flux (empathy) or seek refuge from it (abstraction)? "
    "And is that stance coherent — does the image commit to its orientation, "
    "or does it waver between the two impulses without purpose?"
)

ESSENTIAL_CLAIMS = [
    "Empathy and abstraction are the two poles of human artistic experience. "
    "They are antitheses which in principle are mutually exclusive, but in "
    "practice the history of art is an unceasing disputation between them.",
    "The will to abstraction is NOT a lack of ability. Primitive and "
    "non-Western art that favors geometric abstraction does so from a "
    "differently directed volition, not from inability to represent nature.",
    "Space is the major enemy of all striving after abstraction. The first "
    "thing abstraction suppresses is the representation of depth.",
    "The highest, purest regular art-form (strict abstraction) is peculiar "
    "to peoples at their most primitive cultural level — a causal connection "
    "exists between spiritual dread and geometric rigor.",
    "Worringer derives the concept of 'artistic volition' (Kunstwollen) from "
    "Riegl: art history is a history of volition, not ability. Stylistic "
    "differences reflect different psychic needs, not different skill levels.",
    "Neither impulse is superior. Worringer explicitly opposes the "
    "'European-Classical prejudice' that naturalism represents progress.",
]

ANTI_GOALS = [
    "Must not treat 'abstraction' as a style label for modern abstract art — "
    "Worringer means something much broader and older",
    "Must not grade images on technical skill or representational accuracy",
    "Must not collapse the theory into a simple 'abstract vs. realistic' binary — "
    "the psychological dimension (dread vs. confidence) is essential",
    "Must not ignore the spatial dimension: does the image suppress or embrace depth?",
    "Must not impose empathy-based criteria on images operating from the "
    "abstraction impulse, or vice versa",
]

# Vocabulary Worringer actually uses.
DISTINCTIVE_VOCABULARY = [
    "empathy", "Einfühlung",
    "abstraction", "Abstraktion",
    "artistic volition", "Kunstwollen",
    "dread of space", "Raumscheu",
    "flux of being",
    "crystalline", "geometric regularity",
    "organic", "vitality",
    "irrefragible", "necessary",
    "pantheistic", "transcendental",
    "self-activation", "objectified self-enjoyment",
]

GOOD_CRITIQUE_EXAMPLE = (
    "This image operates firmly from the abstraction impulse. Depth is "
    "suppressed — all elements occupy a single frontal plane with no "
    "atmospheric recession. Forms tend toward geometric regularity: repeated "
    "angular patterns create a crystalline field that resists organic reading. "
    "The image seeks to wrest its elements out of the flux of appearance and "
    "render them stable and necessary. The coherence is strong — nothing in "
    "the image invites empathetic projection or suggests a habitable space. "
    "However, the slight curvilinear intrusion at center-left introduces an "
    "organic note that weakens the abstractive commitment without being "
    "purposeful enough to read as intentional tension between the two impulses."
)

BAD_CRITIQUE_EXAMPLE = (
    "This is an abstract composition with geometric shapes. The abstraction "
    "level is high. The artist has chosen not to represent recognizable "
    "objects, instead focusing on pure form and color."
)
