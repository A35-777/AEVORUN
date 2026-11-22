"""AEVORUN-T1 Neural Model Architecture and Training Utilities.

Compact, learned multi-label neural network trained from scratch on AST feature representations.
Features:
- Residual feed-forward blocks with LayerNorm and GELU activations.
- Multi-label classification head with temperature calibration.
- Zero external pretrained weights; 100% trained from scratch.
- CPU-optimized execution (<1ms latency per function).
"""

import os
import math
import json
import hashlib
from typing import Dict, List, Tuple, Optional, Any
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from aevorun.taxonomy import NUM_SCENARIOS, SCENARIO_NAMES
from aevorun.features import FEATURE_DIM


class TemperatureScaling(nn.Module):
    """Calibrate model confidence via a learned temperature parameter."""
    def __init__(self, init_temperature: float = 1.0):
        super().__init__()
        self.temperature = nn.Parameter(torch.tensor(float(init_temperature), dtype=torch.float32))

    def forward(self, logits: torch.Tensor) -> torch.Tensor:
        temp = torch.clamp(self.temperature, min=0.1, max=5.0)
        return logits / temp


class AevorunT1Net(nn.Module):
    """AEVORUN-T1 Deep Residual Multi-Label Classifier."""

    def __init__(
        self,
        input_dim: int = FEATURE_DIM,
        hidden_dim: int = 128,
        num_classes: int = NUM_SCENARIOS,
        dropout_rate: float = 0.20
    ):
        super().__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.num_classes = num_classes

        # Input projection
        self.fc_in = nn.Linear(input_dim, hidden_dim)
        self.norm1 = nn.LayerNorm(hidden_dim)
        self.act1 = nn.GELU()
        self.drop1 = nn.Dropout(dropout_rate)

        # Residual Block
        self.res_fc1 = nn.Linear(hidden_dim, hidden_dim)
        self.res_norm1 = nn.LayerNorm(hidden_dim)
        self.res_act1 = nn.GELU()
        self.res_drop1 = nn.Dropout(dropout_rate)
        self.res_fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.res_norm2 = nn.LayerNorm(hidden_dim)

        # Bottleneck
        self.fc_mid = nn.Linear(hidden_dim, 64)
        self.norm_mid = nn.LayerNorm(64)
        self.act_mid = nn.GELU()
        self.drop_mid = nn.Dropout(dropout_rate * 0.5)

        # Output head
        self.head = nn.Linear(64, num_classes)
        self.temp_scaler = TemperatureScaling(init_temperature=1.0)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass returning raw uncalibrated logits."""
        # Input layer
        h = self.fc_in(x)
        h = self.norm1(h)
        h = self.act1(h)
        h = self.drop1(h)

        # Residual connection
        residual = h
        res = self.res_fc1(h)
        res = self.res_norm1(res)
        res = self.res_act1(res)
        res = self.res_drop1(res)
        res = self.res_fc2(res)
        res = self.res_norm2(res)
        h = F.gelu(residual + res)

        # Bottleneck
        h = self.fc_mid(h)
        h = self.norm_mid(h)
        h = self.act_mid(h)
        h = self.drop_mid(h)

        # Head
        logits = self.head(h)
        return logits

    def forward_calibrated(self, x: torch.Tensor) -> torch.Tensor:
        """Returns calibrated probabilities via sigmoid(logits / temperature)."""
        logits = self.forward(x)
        calibrated_logits = self.temp_scaler(logits)
        return torch.sigmoid(calibrated_logits)

    def get_parameter_count(self) -> int:
        """Total trainable parameters."""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)


class MultiLabelFocalLoss(nn.Module):
    """Multi-label Focal Loss to address severe class imbalance in temporal edge cases."""

    def __init__(self, alpha: float = 0.65, gamma: float = 2.0, pos_weight: Optional[torch.Tensor] = None):
        super().__init__()
        self.alpha = alpha
        self.gamma = gamma
        self.pos_weight = pos_weight

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        # Standard BCE with logits
        bce_loss = F.binary_cross_entropy_with_logits(
            logits, targets, pos_weight=self.pos_weight, reduction="none"
        )
        probs = torch.sigmoid(logits)
        p_t = targets * probs + (1 - targets) * (1 - probs)
        alpha_t = targets * self.alpha + (1 - targets) * (1 - self.alpha)
        focal_weight = alpha_t * torch.pow((1.0 - p_t), self.gamma)
        loss = focal_weight * bce_loss
        return loss.mean()


class AevorunModelWrapper:
    """Production wrapper for AEVORUN-T1 PyTorch model for training, inference, and serialization."""

    def __init__(self, model: Optional[AevorunT1Net] = None):
        self.model = model or AevorunT1Net()
        self.is_fitted = False
        self.thresholds: np.ndarray = np.full(NUM_SCENARIOS, 0.45, dtype=np.float32)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Given (N, FEATURE_DIM) numpy array, returns (N, NUM_SCENARIOS) calibrated probabilities."""
        self.model.eval()
        with torch.no_grad():
            x_t = torch.tensor(X, dtype=torch.float32)
            probs = self.model.forward_calibrated(x_t).cpu().numpy()
        return probs

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict binary multi-hot vectors using calibrated thresholds."""
        probs = self.predict_proba(X)
        return (probs >= self.thresholds).astype(np.int32)

    def save_checkpoint(self, path: str, metadata: Optional[Dict[str, Any]] = None):
        """Save complete model checkpoint, weights, thresholds, and metadata."""
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        checkpoint = {
            "model_name": "AEVORUN-T1",
            "model_version": "1.0.0",
            "state_dict": self.model.state_dict(),
            "input_dim": self.model.input_dim,
            "hidden_dim": self.model.hidden_dim,
            "num_classes": self.model.num_classes,
            "param_count": self.model.get_parameter_count(),
            "thresholds": self.thresholds.tolist(),
            "metadata": metadata or {},
        }
        torch.save(checkpoint, path)

    @classmethod
    def load_checkpoint(cls, path: str) -> "AevorunModelWrapper":
        """Load AEVORUN-T1 model from saved checkpoint file."""
        checkpoint = torch.load(path, map_location="cpu", weights_only=True)
        model = AevorunT1Net(
            input_dim=checkpoint.get("input_dim", FEATURE_DIM),
            hidden_dim=checkpoint.get("hidden_dim", 128),
            num_classes=checkpoint.get("num_classes", NUM_SCENARIOS)
        )
        model.load_state_dict(checkpoint["state_dict"])
        model.eval()

        wrapper = cls(model=model)
        wrapper.is_fitted = True
        if "thresholds" in checkpoint:
            wrapper.thresholds = np.array(checkpoint["thresholds"], dtype=np.float32)
        return wrapper

    def compute_checksum(self, path: str) -> str:
        """Compute SHA256 checksum of saved checkpoint."""
        hasher = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

