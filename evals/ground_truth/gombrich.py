"""
Ground truth for Ernst Gombrich's "The Sense of Order" (1979).

Gombrich's book is about decorative art and the psychology of pattern.
His subject is specifically ornament, decoration, and the perceptual
mechanisms behind our response to repeated pattern and ordered design.

This makes Gombrich a specialized critic: best suited for images with
pattern, repetition, tessellation, border design, and decorative
structure. Less suited for figurative composition or single-focal-point
images.

Core thesis: our perception has a built-in "sense of order" — we
actively monitor our environment for regularity and deviations from it.
Decoration exploits this monitoring system. The pleasure of pattern comes
from the interplay between expectation and surprise, between redundancy
and information.
"""

CORE_CONCEPTS = {
    "sense_of_order": {
        "definition": (
            "Humans have an innate drive to seek and impose order on their "
            "perceptual environment. This 'sense of order' is not passive "
            "aesthetic preference but an active monitoring system that "
            "detects regularity, expects continuation, and notices deviations."
        ),
        "implication_for_art": (
            "Decoration works by setting up expectations through pattern "
            "and then either confirming them (providing comfort and "
            "redundancy) or breaking them (providing interest and information)."
        ),
    },
    "redundancy_and_information": {
        "definition": (
            "A perfectly regular pattern is maximally redundant — once you "
            "see the unit, you can predict the rest. It is ordered but "
            "boring. A completely random field has maximum information but "
            "no perceivable order. Good decoration balances redundancy "
            "(order, predictability) with information (surprise, variation)."
        ),
        "spectrum": [
            "Maximum redundancy: simple repeat, wallpaper, grid → restful, dull",
            "Balanced: pattern with intentional variation → engaging",
            "Maximum information: randomness → perceived as noise, not pattern",
        ],
    },
    "monotony_and_variety": {
        "definition": (
            "The fundamental tension in decorative art. Too much monotony "
            "and the pattern becomes wallpaper — the eye habituates and "
            "stops attending. Too much variety and the pattern collapses "
            "into chaos — the eye cannot find footing."
        ),
        "what_to_look_for": [
            "Can the eye detect the repeat unit?",
            "Does the pattern sustain attention or does the eye habituate quickly?",
            "Are variations within the pattern purposeful or disruptive?",
        ],
    },
    "grading_of_complexity": {
        "definition": (
            "Gombrich identifies a spectrum from simple geometric repeat "
            "through increasingly complex interlace, arabesque, and "
            "grotesque. Each level engages the sense of order differently."
        ),
        "levels": [
            "Simple repeat (frieze, grid)",
            "Alternation and mirror symmetry",
            "Interlace and over-under patterns",
            "Arabesque and continuous scroll",
            "Grotesque and hybrid forms",
        ],
    },
    "frame_and_fill": {
        "definition": (
            "The relationship between the containing structure (frame, "
            "border, field boundary) and the pattern that fills it. "
            "Gombrich argues this is a fundamental organizing principle "
            "of all decorative art."
        ),
    },
}

ESSENTIAL_CLAIMS = [
    "The sense of order is perceptual, not cultural. The drive to detect "
    "regularity and deviation is a basic feature of human perception, not "
    "a learned preference.",
    "Decoration exploits the expectation-monitoring system: pattern sets up "
    "expectations, and the aesthetic response depends on how those expectations "
    "are met, varied, or broken.",
    "The balance between redundancy and information is the central diagnostic. "
    "Too much of either fails.",
    "Gombrich explicitly connects to information theory: pattern is redundancy "
    "(predictable), variation is information (surprising), and good decoration "
    "optimizes the ratio.",
    "The psychology of habituation matters: the eye adapts to regular pattern "
    "and stops attending. Sustained interest requires calibrated disruption.",
    "Gombrich defends decorative art against the modernist prejudice that "
    "treats it as inferior to 'fine' art. Pattern and ornament engage "
    "genuine perceptual and aesthetic faculties.",
]

ANTI_GOALS = [
    "Must not apply this framework to images without pattern or repetition — "
    "Gombrich's theory is specifically about decorative order",
    "Must not reduce the analysis to 'is the pattern good?' — the diagnostic "
    "is about redundancy vs. information, monotony vs. variety",
    "Must not ignore the frame/field relationship — how the pattern meets "
    "its boundaries matters",
    "Must not treat complexity as automatically better — simple patterns can "
    "be more appropriate depending on context",
    "Must not confuse Gombrich's perceptual analysis with historical "
    "classification of ornamental styles",
]

DISTINCTIVE_VOCABULARY = [
    "sense of order", "monitoring",
    "redundancy", "information",
    "monotony", "variety",
    "habituation", "adaptation",
    "repeat unit", "frieze", "grid",
    "interlace", "arabesque", "grotesque",
    "frame and fill",
    "expectation", "surprise",
    "grading of complexity",
]

GOOD_CRITIQUE_EXAMPLE = (
    "The pattern operates at moderate complexity — an alternating repeat with "
    "mirror symmetry along the horizontal axis. Redundancy is high: the repeat "
    "unit is immediately legible and the eye predicts continuation accurately. "
    "This creates a restful field, but habituation risk is real — after a few "
    "units, the eye has nothing new to discover. The variation introduced in "
    "the third row (rotated unit, shifted alignment) provides a useful "
    "information spike, but it disrupts the frame-fill relationship: the "
    "shifted elements no longer respect the border geometry, creating an "
    "unresolved tension between the pattern logic and its containment."
)

BAD_CRITIQUE_EXAMPLE = (
    "The pattern is visually interesting with a good sense of rhythm. The "
    "repetition creates a pleasing effect and the overall design is well "
    "crafted. The decorative quality is high."
)
