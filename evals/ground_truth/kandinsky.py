"""
Ground truth for Wassily Kandinsky's "Point and Line to Plane" (1926).

Kandinsky treats point, line, and the basic plane as a formal grammar —
elements with inherent expressive properties that interact through tension,
direction, and rhythm. This is NOT just geometry; every element carries
energy, temperature, and relational force.

Key distinction from other formalists: Kandinsky assigns quasi-physical
properties to abstract elements. A horizontal line is "cold"; a vertical
is "warm." A point is concentrated energy. These are not metaphors for him
but structural descriptions of visual experience.
"""

# The three fundamental elements and their properties.
ELEMENTS = {
    "point": {
        "definition": (
            "The point is the proto-element of painting. In its geometric "
            "essence it is the ultimate and most singular union of silence "
            "and speech. It is the result of the initial collision of the "
            "tool with the material plane. It is concentric tension."
        ),
        "properties": [
            "Concentric (tension directed inward)",
            "Static in isolation, but becomes dynamic through placement",
            "Size transforms it: a growing point becomes a plane",
            "The boundary between point and plane is not fixed but contextual",
        ],
        "what_to_look_for": [
            "Where are the concentrated visual events in the image?",
            "Do point-like elements function as anchors or accents?",
            "Is there a hierarchy among point events, or are they scattered?",
        ],
    },
    "line": {
        "definition": (
            "The geometric line is an invisible thing. It is the track made "
            "by the moving point. It arises from movement — through the "
            "destruction of the point's supreme self-contained repose."
        ),
        "types": {
            "horizontal": {
                "character": "cold, flat, capable of infinite extension",
                "temperature": "cold",
            },
            "vertical": {
                "character": "warm, height, active, aspiring",
                "temperature": "warm",
            },
            "diagonal": {
                "character": "equal parts warm and cold, tension between the two",
                "temperature": "warm-cold",
            },
            "curved": {
                "character": "deflected straight line under continuous lateral pressure",
                "temperature": "varies with curvature",
            },
            "angular": {
                "character": "created by two forces; the angle determines the temperature",
                "subtypes": {
                    "acute (45°)": "sharpest, most active, warmest",
                    "right (90°)": "coldest of the angular, most restrained",
                    "obtuse (135°)": "weakest, most passive",
                },
            },
        },
        "what_to_look_for": [
            "What are the dominant line directions and what energy do they create?",
            "Do line types contrast with each other (warm vs. cold)?",
            "Is there rhythmic variation or monotonous repetition?",
            "Do lines create directional pull or remain static?",
        ],
    },
    "basic_plane": {
        "definition": (
            "The basic plane (Grundfläche) is the material surface that "
            "receives the content of the work. Its boundaries create "
            "tensions that interact with every element placed upon it."
        ),
        "properties": [
            "The BP has four boundaries creating inherent tensions",
            "Top is 'looseness' and 'lightness'; bottom is 'density' and 'heaviness'",
            "Left is associated with 'distance' and 'going away'; right with "
            "'home' and 'coming'",
            "The center is the point of least tension",
            "Square BP: relatively objective, equal tension on all sides",
            "Horizontal BP: cold, the elements feel heavier",
            "Vertical BP: warm, the elements feel lighter and more active",
        ],
        "what_to_look_for": [
            "How does the format (aspect ratio) of the image affect the elements?",
            "Are elements placed where the BP's inherent tensions support or "
            "contradict their own energy?",
            "Does the image use the edges and center of the BP intentionally?",
        ],
    },
}

# Kandinsky's overarching compositional principles.
COMPOSITIONAL_PRINCIPLES = [
    "Counterpoint: elements should create structured opposition, not chaos",
    "Tension: the internal force of an element, arising from its direction, "
    "weight, and relation to the basic plane",
    "Rhythm: repetition and variation of elements creating temporal experience "
    "across the visual field",
    "Constructive tension vs. destructive tension: the former builds visual "
    "coherence, the latter produces noise",
]

ESSENTIAL_CLAIMS = [
    "Every pictorial element has inherent expressive force independent of "
    "representation — a diagonal line IS tense, not just reminiscent of tension.",
    "Temperature (warm/cold) is a primary organizing concept: verticals are warm, "
    "horizontals are cold, diagonals are mixed.",
    "The basic plane is not a neutral container but an active participant with "
    "its own force field (top=light, bottom=heavy, left=away, right=home).",
    "Composition is constructive counterpoint among tensions, not decorative "
    "arrangement of shapes.",
    "The point-to-line-to-plane progression describes transformation of energy, "
    "not just geometric complexity.",
    "Size context matters: a 'point' that grows large enough becomes a 'plane'; "
    "boundaries between elements are relative, not absolute.",
]

ANTI_GOALS = [
    "Must not reduce the analysis to naming geometric shapes",
    "Must not ignore the temperature/energy properties Kandinsky assigns to "
    "directions and forms",
    "Must not treat the basic plane as neutral — its format and boundaries matter",
    "Must not confuse Kandinsky's system with generic 'elements and principles of design'",
    "Must not center the critique on representational content when the image "
    "operates abstractly",
]

DISTINCTIVE_VOCABULARY = [
    "tension", "counterpoint", "temperature",
    "warm", "cold",
    "concentric", "eccentric",
    "basic plane", "Grundfläche",
    "inner necessity",
    "constructive", "lyrical", "dramatic",
    "angular", "free curve",
    "accent", "rhythm",
    "force", "repose",
]

GOOD_CRITIQUE_EXAMPLE = (
    "The dominant line movement is diagonal — warm-cold tension pulling from "
    "lower-left toward upper-right, which the vertical basic plane amplifies "
    "into a strong ascending force. Two point-concentrations anchor the "
    "composition: one near center (low tension, stable) and one at upper-right "
    "(high tension against the BP boundary). The counterpoint between the "
    "diagonal thrust and the cold horizontal band at bottom creates structured "
    "opposition. However, the curved elements in the middle zone lack clear "
    "directional purpose — they add complexity without constructive tension."
)

BAD_CRITIQUE_EXAMPLE = (
    "The image uses circles, lines, and rectangles arranged on a white "
    "background. The geometric shapes create an abstract pattern. The "
    "composition has movement and energy."
)
