"""Main AEVORUN Developer SDK Interface.

Provides the primary user-facing `Aevorun` class for analyzing Python source code,
predicting temporal test scenarios, and prioritizing edge cases completely offline.
"""

import os
import json
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import numpy as np

from aevorun.taxonomy import TAXONOMY, SCENARIO_NAMES, NUM_SCENARIOS, Scenario
from aevorun.features import (
    extract_function_features,
    ExtractedFeatures,
    CodeEvidence,
    FEATURE_DIM,
)
from aevorun.model import AevorunModelWrapper, AevorunT1Net


@dataclass
class EvidenceItem:
    """Serializable code evidence explanation for a scenario."""
    feature: str
    line: int
    snippet: str
    explanation: str


@dataclass
class PredictedScenario:
    """A prioritized temporal test scenario prediction."""
    id: int
    name: str
    score: float
    rank: int
    description: str
    recommended_test_dates: List[str]
    evidence: List[EvidenceItem] = field(default_factory=list)


@dataclass
class FunctionAnalysis:
    """Analysis result for an individual Python function."""
    function_name: str
    lines_of_code: int
    is_temporal: bool
    is_valid_syntax: bool
    unsupported_reason: Optional[str]
    scenarios: List[PredictedScenario] = field(default_factory=list)
    raw_scores: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AnalysisResult:
    """Overall result from analyzing a code snippet or file."""
    source_target: str
    functions: List[FunctionAnalysis] = field(default_factory=list)
    model_version: str = "AEVORUN-T1"

    @property
    def scenarios(self) -> List[PredictedScenario]:
        """Convenience accessor for scenarios of the primary/first analyzed function."""
        if self.functions:
            return self.functions[0].scenarios
        return []

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


class Aevorun:
    """AEVORUN Temporal Test-Scenario Prioritization Engine.

    Finds the time-related tests your code is most likely to need.
    Runs completely offline using the compact AEVORUN-T1 neural model.
    """

    DEFAULT_CHECKPOINT_PATH = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "model",
        "checkpoints",
        "aevorun_t1.pt"
    )

    def __init__(self, checkpoint_path: Optional[str] = None):
        self.checkpoint_path = checkpoint_path or self.DEFAULT_CHECKPOINT_PATH
        self._wrapper: Optional[AevorunModelWrapper] = None
        self._load_model()

    def _load_model(self):
        """Load checkpoint if available, or initialize default model."""
        if os.path.exists(self.checkpoint_path):
            try:
                self._wrapper = AevorunModelWrapper.load_checkpoint(self.checkpoint_path)
                return
            except Exception as e:
                # Fall back to untrained/default initialized architecture
                pass
        self._wrapper = AevorunModelWrapper()

    def analyze_source(
        self,
        source_code: str,
        function_name: Optional[str] = None,
        top_k: int = 5,
        threshold: float = 0.20
    ) -> AnalysisResult:
        """Analyze a Python source code string.

        Args:
            source_code: Python source code string.
            function_name: Optional target function name to filter.
            top_k: Number of top prioritized scenarios to return per function.
            threshold: Minimum confidence score to include in top scenarios.

        Returns:
            AnalysisResult with ranked scenarios and evidence.
        """
        extracted_list = extract_function_features(
            source_code=source_code, target_function_name=function_name
        )
        fn_analyses: List[FunctionAnalysis] = []

        for ext in extracted_list:
            if not ext.is_valid_syntax:
                fn_analyses.append(
                    FunctionAnalysis(
                        function_name=ext.function_name,
                        lines_of_code=ext.lines_of_code,
                        is_temporal=False,
                        is_valid_syntax=False,
                        unsupported_reason=ext.unsupported_reason,
                        scenarios=[],
                        raw_scores={}
                    )
                )
                continue

            # Run inference
            feat_vec = np.expand_dims(ext.feature_vector, axis=0)
            probs = self._wrapper.predict_proba(feat_vec)[0]  # shape: (NUM_SCENARIOS,)

            # If function has zero temporal features, suppress edge cases unless score is unusually high
            if not ext.is_temporal:
                probs = probs * 0.15

            # Rank scenarios
            ranked_indices = np.argsort(-probs)
            raw_scores = {SCENARIO_NAMES[i]: float(probs[i]) for i in range(NUM_SCENARIOS)}

            # Build evidence map
            evidence_items = [
                EvidenceItem(
                    feature=ev.feature_name,
                    line=ev.line_number,
                    snippet=ev.snippet,
                    explanation=ev.description
                )
                for ev in ext.evidence
            ]

            scenarios: List[PredictedScenario] = []
            rank = 1
            for idx in ranked_indices:
                score = float(probs[idx])
                if score < threshold and len(scenarios) >= 3:
                    # Keep at least top 3 if top_k allows, or stop if below threshold
                    break
                if len(scenarios) >= top_k:
                    break

                scen_meta = TAXONOMY[SCENARIO_NAMES[idx]]
                scenarios.append(
                    PredictedScenario(
                        id=scen_meta.id,
                        name=scen_meta.name,
                        score=round(score, 4),
                        rank=rank,
                        description=scen_meta.description,
                        recommended_test_dates=scen_meta.recommended_test_dates,
                        evidence=evidence_items
                    )
                )
                rank += 1

            fn_analyses.append(
                FunctionAnalysis(
                    function_name=ext.function_name,
                    lines_of_code=ext.lines_of_code,
                    is_temporal=ext.is_temporal,
                    is_valid_syntax=True,
                    unsupported_reason=None,
                    scenarios=scenarios,
                    raw_scores=raw_scores
                )
            )

        return AnalysisResult(
            source_target="<string>",
            functions=fn_analyses,
            model_version="AEVORUN-T1"
        )

    def analyze_file(
        self,
        file_path: Union[str, Path],
        function_name: Optional[str] = None,
        top_k: int = 5,
        threshold: float = 0.20
    ) -> AnalysisResult:
        """Analyze a Python file from disk."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Source file not found: {file_path}")

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(path, "r", encoding="latin-1") as f:
                content = f.read()

        res = self.analyze_source(
            source_code=content,
            function_name=function_name,
            top_k=top_k,
            threshold=threshold
        )
        res.source_target = str(path)
        return res

