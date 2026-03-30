"""autocritic: critic-card-driven image evaluation using art theory lenses."""

from autocritic.critic import (
    CriticCard,
    CritiqueResult,
    load_critic,
    critique_image,
    compare_iterations,
)
from autocritic.scoring import ScoredCritique, score_critique, compare_scores
from autocritic.translator import ParamSpace, ParamSpec, TranslationResult

__all__ = [
    "CriticCard",
    "CritiqueResult",
    "load_critic",
    "critique_image",
    "compare_iterations",
    "ScoredCritique",
    "score_critique",
    "compare_scores",
    "ParamSpace",
    "ParamSpec",
    "TranslationResult",
]

__version__ = "0.1.0"
