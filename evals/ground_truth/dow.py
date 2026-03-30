"""
Ground truth for Arthur Wesley Dow's "Composition" (1899/1913).

Dow's system is explicitly pedagogical and operational. He reduces visual
art to three elements (Line, Notan, Color) and five principles of
harmony-building. This makes it a directly "generator-friendly" theory —
his categories map cleanly to image properties that a software system
can manipulate.

Key distinction: Dow's framework comes from his synthesis of Japanese
design principles with Western art education. His concept of "notan"
(dark-light massing) is borrowed from Japanese aesthetic tradition and
is central to his system in a way that is unique among formalist
theorists.
"""

# The three elements of visual art according to Dow.
ELEMENTS = {
    "line": {
        "definition": (
            "Line is the first element of pictorial expression. It includes "
            "contour, boundary, direction, and the character of marks. Line "
            "is not just outline but any use of linear movement as a "
            "compositional force."
        ),
        "aspects": [
            "Contour and boundary of forms",
            "Direction and flow across the composition",
            "Character (thick/thin, smooth/rough, continuous/broken)",
            "Line as structure (the skeleton of the design)",
        ],
        "what_to_look_for": [
            "Do lines create clear directional flow?",
            "Is there variety in line character, or is it monotonous?",
            "Do lines define forms through contour or through implied boundaries?",
        ],
    },
    "notan": {
        "definition": (
            "Notan is the Japanese word for dark-light. It refers to the "
            "arrangement of dark and light masses as a compositional element "
            "independent of color or representation. A good notan pattern "
            "reads as a strong design even when stripped of all other qualities."
        ),
        "aspects": [
            "Two-value design (just dark and light, no middle tones)",
            "Three-value and four-value progressions",
            "The shape of light masses and dark masses as positive design",
            "Notan as independent of color — the dark-light structure carries "
            "the composition's backbone",
        ],
        "what_to_look_for": [
            "If you squint or desaturate, does a clear dark-light pattern emerge?",
            "Are the dark masses and light masses interesting shapes on their own?",
            "Does the notan create visual flow or does it fragment?",
            "How many value steps are being used, and is that number intentional?",
        ],
    },
    "color": {
        "definition": (
            "Color is the third element, built on top of line and notan. "
            "Dow treats color as subordinate to dark-light structure — "
            "color should enhance the notan pattern, not replace it."
        ),
        "aspects": [
            "Hue relationships (harmony, contrast, dominance)",
            "Color as an extension of notan (every color has a value)",
            "Color schemes and their emotional associations",
            "Subordination of color to the overall compositional design",
        ],
        "what_to_look_for": [
            "Does the color support or undermine the notan structure?",
            "Is there a dominant color relationship or unresolved competition?",
            "Would the composition hold up if reduced to grayscale?",
        ],
    },
}

# Dow's five principles of harmony-building (ways of creating order).
PRINCIPLES = {
    "opposition": {
        "definition": (
            "The meeting of lines or forms at right angles or in strong "
            "contrast. Opposition creates energy and structural clarity."
        ),
        "example": "A vertical meeting a horizontal; a dark mass against a light ground.",
    },
    "transition": {
        "definition": (
            "Connection through curved or intermediate elements that lead "
            "the eye smoothly from one area to another."
        ),
        "example": "A curve connecting two straight elements; a gradation bridging two values.",
    },
    "subordination": {
        "definition": (
            "One element dominates; others serve. Without subordination, "
            "the design has no hierarchy and no focal logic."
        ),
        "example": "One large dark mass governs the page; smaller elements support it.",
    },
    "repetition": {
        "definition": (
            "Recurrence of similar elements creating rhythm and visual "
            "continuity across the field."
        ),
        "example": "Repeated verticals; echoing curves; recurring intervals of dark.",
    },
    "symmetry": {
        "definition": (
            "Balance through equal distribution, either exact mirror or "
            "approximate equivalence. Dow treats symmetry as one option "
            "among several, not a default requirement."
        ),
        "example": "A centered composition with balanced flanking elements.",
    },
}

ESSENTIAL_CLAIMS = [
    "Notan (dark-light structure) is independent of and more fundamental than "
    "color. A composition should work in two values before color is added.",
    "The three elements (Line, Notan, Color) form a progression: Line first, "
    "then Notan, then Color. Each builds on the previous.",
    "Composition is 'harmony-building' — the act of creating visual order "
    "through deliberate arrangement of elements.",
    "Dow's five principles (Opposition, Transition, Subordination, Repetition, "
    "Symmetry) are 'ways of creating harmony,' not rules to follow mechanically.",
    "Japanese design principles are integral to Dow's system, especially the "
    "concept of notan and the emphasis on design as arrangement rather than "
    "imitation of nature.",
    "Dow explicitly rejects academic drawing-from-casts pedagogy in favor of "
    "design-first training. The purpose of art is not imitation but "
    "'the expression of the artist's thought in a beautiful way.'",
]

ANTI_GOALS = [
    "Must not ignore notan — it is the most distinctive element of Dow's system",
    "Must not treat the five principles as a checklist to satisfy simultaneously",
    "Must not collapse Dow's framework into generic 'elements and principles of "
    "design' — his specific debt to Japanese aesthetics matters",
    "Must not elevate color above notan in the hierarchy",
    "Must not treat representational accuracy as a criterion — Dow explicitly "
    "subordinates imitation to design",
]

DISTINCTIVE_VOCABULARY = [
    "notan", "dark-and-light",
    "harmony-building", "spacing",
    "opposition", "transition", "subordination", "repetition", "symmetry",
    "composition in values",
    "line quality", "brush practice",
    "two-value", "three-value",
    "massing",
]

GOOD_CRITIQUE_EXAMPLE = (
    "The notan structure is strong in two values — dark masses form clear, "
    "interesting shapes against the light ground, and the composition reads "
    "cleanly even in squinted view. Subordination is effective: one dominant "
    "dark mass anchors the upper-left, with secondary darks creating rhythm "
    "through repetition of similar intervals. Line quality supports the notan "
    "by defining boundaries without competing for attention. The weak point is "
    "transition — the jump from the dominant mass to the lower-right quadrant "
    "is abrupt, with no curved or graduated element to guide the eye."
)

BAD_CRITIQUE_EXAMPLE = (
    "The image has a nice composition with good use of contrast. The dark "
    "and light areas are well balanced. The overall design is pleasing and "
    "the artist shows good control of the medium."
)
