"""AEVORUN: Learned Temporal Test-Scenario Prioritization.

Model: AEVORUN-T1
Find the time-related tests your code is most likely to need.
"""

__version__ = "0.1.0"
__model_version__ = "AEVORUN-T1"

from aevorun.taxonomy import Scenario, TAXONOMY
from aevorun.core import Aevorun, AnalysisResult, PredictedScenario

__all__ = [
    "Aevorun",
    "AnalysisResult",
    "PredictedScenario",
    "Scenario",
    "TAXONOMY",
    "__version__",
    "__model_version__",
]

