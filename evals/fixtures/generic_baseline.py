"""
The generic baseline: a deliberately bland critique that any design coach
could produce about any image. This is the foil for lens_specificity evals.

If a critic card or critique output sounds too similar to this, it has
drifted away from its theoretical source and toward generic art talk.
"""

GENERIC_CRITIQUE = """\
The composition shows good use of visual elements. The balance between
different areas creates an effective overall design. Color choices support
the mood of the piece. There is a clear focal point that draws the eye.

The artist demonstrates solid understanding of design principles. The use
of contrast creates visual interest. Negative space is handled well.
The overall rhythm of the piece guides the viewer through the composition.

Strengths:
- Strong sense of balance
- Effective use of contrast
- Good focal point placement
- Harmonious color palette

Areas for improvement:
- Consider strengthening the visual hierarchy
- Some areas could benefit from more variety
- The edges of the composition could be more resolved
- Think about the relationship between foreground and background

Next steps:
- Refine the focal area
- Add more visual interest to secondary areas
- Consider the overall flow of the composition
- Experiment with stronger contrast in key areas
"""

GENERIC_CRITERIA = [
    "balance",
    "contrast",
    "focal point",
    "color harmony",
    "visual hierarchy",
    "rhythm",
    "negative space",
    "unity",
]

GENERIC_VOCABULARY = [
    "composition", "balance", "contrast", "focal point", "harmony",
    "rhythm", "negative space", "visual interest", "hierarchy",
    "flow", "unity", "variety", "emphasis", "proportion",
    "effective", "strong", "dynamic", "engaging",
]
