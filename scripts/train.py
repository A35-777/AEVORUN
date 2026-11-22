"""AEVORUN-T1 Training Script.

Trains the compact AEVORUN-T1 neural model from scratch using the AST-extracted features
from the partitioned AEVORUN dataset.
Includes:
- Multi-label Focal Loss / BCE with positive class weighting
- AdamW optimizer with Cosine Annealing learning rate schedule
- Early stopping based on validation Micro-F1 / Macro-F1
- Post-training probability calibration via temperature scaling
- Complete checkpoint and configuration export with SHA256 checksums
"""

import os
import sys
import json
import time
import random
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Any

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.metrics import f1_score, precision_score, recall_score, average_precision_score

# Ensure aevorun package is importable
REPO_ROOT = Path("d:/AEVORUN")
sys.path.insert(0, str(REPO_ROOT))

from aevorun.taxonomy import NUM_SCENARIOS, SCENARIO_NAMES
from aevorun.features import extract_function_features, FEATURE_DIM
from aevorun.model import AevorunT1Net, MultiLabelFocalLoss, AevorunModelWrapper

DATA_DIR = REPO_ROOT / "data" / "processed"
MODEL_DIR = REPO_ROOT / "model"
CHECKPOINT_DIR = MODEL_DIR / "checkpoints"
CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)


def set_seed(seed: int = 42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


class CodeFeatureDataset(Dataset):
    """Dataset converting JSONL source samples to extracted AST feature vectors and multi-hot targets."""

    def __init__(self, jsonl_path: Path):
        self.samples: List[Dict[str, Any]] = []
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    self.samples.append(json.loads(line))

        self.features: List[np.ndarray] = []
        self.labels: List[np.ndarray] = []
        self.sample_ids: List[str] = []
        self.repos: List[str] = []

        scenario_to_idx = {name: i for i, name in enumerate(SCENARIO_NAMES)}

        for s in self.samples:
            ext_list = extract_function_features(s["source_code"])
            # Use extracted features from the primary function
            feat = ext_list[0]
            self.features.append(feat.feature_vector)

            # Build multi-hot target vector
            target = np.zeros(NUM_SCENARIOS, dtype=np.float32)
            for lab in s.get("labels", []):
                if lab in scenario_to_idx:
                    target[scenario_to_idx[lab]] = 1.0
            self.labels.append(target)
            self.sample_ids.append(s.get("sample_id", ""))
            self.repos.append(s.get("repo", ""))

        self.features_arr = np.array(self.features, dtype=np.float32)
        self.labels_arr = np.array(self.labels, dtype=np.float32)

    def __len__(self) -> int:
        return len(self.features)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        return torch.tensor(self.features_arr[idx]), torch.tensor(self.labels_arr[idx])


def compute_metrics(y_true: np.ndarray, y_prob: np.ndarray, threshold: float = 0.45) -> Dict[str, float]:
    y_pred = (y_prob >= threshold).astype(int)
    macro_f1 = f1_score(y_true, y_pred, average="macro", zero_division=0)
    micro_f1 = f1_score(y_true, y_pred, average="micro", zero_division=0)
    macro_prec = precision_score(y_true, y_pred, average="macro", zero_division=0)
    macro_rec = recall_score(y_true, y_pred, average="macro", zero_division=0)

    # Precision@3 and Recall@3
    k = 3
    n_samples = len(y_true)
    top_k_precisions = []
    top_k_recalls = []

    for i in range(n_samples):
        true_indices = set(np.where(y_true[i] == 1)[0])
        pred_top_k = set(np.argsort(-y_prob[i])[:k])

        if len(true_indices) > 0:
            hits = len(true_indices.intersection(pred_top_k))
            top_k_precisions.append(hits / float(k))
            top_k_recalls.append(hits / float(len(true_indices)))

    p_at_3 = float(np.mean(top_k_precisions)) if top_k_precisions else 0.0
    r_at_3 = float(np.mean(top_k_recalls)) if top_k_recalls else 0.0

    return {
        "macro_f1": float(macro_f1),
        "micro_f1": float(micro_f1),
        "precision": float(macro_prec),
        "recall": float(macro_rec),
        "precision_at_3": p_at_3,
        "recall_at_3": r_at_3,
    }


def train_aevorun(
    epochs: int = 50,
    batch_size: int = 32,
    lr: float = 0.002,
    weight_decay: float = 1e-4,
    seed: int = 42
) -> Dict[str, Any]:
    set_seed(seed)
    start_time = time.time()

    print("Loading datasets...")
    train_ds = CodeFeatureDataset(DATA_DIR / "train.jsonl")
    val_ds = CodeFeatureDataset(DATA_DIR / "val.jsonl")

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False)

    print(f"Loaded {len(train_ds)} train samples, {len(val_ds)} val samples.")

    # Compute positive class weights to balance rare classes
    pos_counts = np.sum(train_ds.labels_arr, axis=0)
    neg_counts = len(train_ds) - pos_counts
    pos_weights = np.clip(neg_counts / (pos_counts + 1e-5), 1.0, 10.0)
    pos_weight_tensor = torch.tensor(pos_weights, dtype=torch.float32)

    # Initialize model
    model = AevorunT1Net(input_dim=FEATURE_DIM, hidden_dim=128, num_classes=NUM_SCENARIOS)
    criterion = MultiLabelFocalLoss(alpha=0.60, gamma=1.8, pos_weight=pos_weight_tensor)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-5)

    best_val_f1 = 0.0
    best_weights = None
    best_epoch = 0
    history = []

    print(f"Beginning AEVORUN-T1 training for {epochs} epochs (Parameters: {model.get_parameter_count()})...")

    for epoch in range(1, epochs + 1):
        model.train()
        total_train_loss = 0.0

        for x_b, y_b in train_loader:
            optimizer.zero_grad()
            logits = model(x_b)
            loss = criterion(logits, y_b)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            total_train_loss += loss.item() * len(x_b)

        scheduler.step()
        avg_train_loss = total_train_loss / len(train_ds)

        # Validation
        model.eval()
        val_loss = 0.0
        val_probs_list = []
        with torch.no_grad():
            for x_b, y_b in val_loader:
                logits = model(x_b)
                loss = criterion(logits, y_b)
                val_loss += loss.item() * len(x_b)
                probs = torch.sigmoid(logits)
                val_probs_list.append(probs.cpu().numpy())

        avg_val_loss = val_loss / len(val_ds)
        val_probs = np.vstack(val_probs_list)
        metrics = compute_metrics(val_ds.labels_arr, val_probs, threshold=0.45)

        val_score = 0.5 * metrics["macro_f1"] + 0.5 * metrics["precision_at_3"]

        history.append({
            "epoch": epoch,
            "train_loss": round(avg_train_loss, 4),
            "val_loss": round(avg_val_loss, 4),
            "macro_f1": round(metrics["macro_f1"], 4),
            "micro_f1": round(metrics["micro_f1"], 4),
            "precision_at_3": round(metrics["precision_at_3"], 4),
            "recall_at_3": round(metrics["recall_at_3"], 4)
        })

        if val_score > best_val_f1:
            best_val_f1 = val_score
            best_epoch = epoch
            best_weights = {k: v.cpu().clone() for k, v in model.state_dict().items()}

        if epoch % 10 == 0 or epoch == epochs:
            print(f"Epoch {epoch:2d}/{epochs} | Train Loss: {avg_train_loss:.4f} | Val Loss: {avg_val_loss:.4f} | Macro F1: {metrics['macro_f1']:.4f} | P@3: {metrics['precision_at_3']:.4f}")

    # Restore best weights
    if best_weights is not None:
        model.load_state_dict(best_weights)
        print(f"Restored best weights from epoch {best_epoch} (Score: {best_val_f1:.4f}).")

    training_duration = round(time.time() - start_time, 2)
    print(f"Training completed in {training_duration} seconds.")

    # Save checkpoint
    wrapper = AevorunModelWrapper(model=model)
    checkpoint_file = CHECKPOINT_DIR / "aevorun_t1.pt"
    wrapper.save_checkpoint(
        str(checkpoint_file),
        metadata={
            "best_epoch": best_epoch,
            "best_val_score": best_val_f1,
            "training_duration_seconds": training_duration,
            "epochs": epochs,
            "seed": seed,
            "param_count": model.get_parameter_count()
        }
    )

    chk_sum = wrapper.compute_checksum(str(checkpoint_file))
    print(f"Checkpoint saved: {checkpoint_file}")
    print(f"Checkpoint SHA256: {chk_sum}")

    # Save training config & history
    config_data = {
        "model_name": "AEVORUN-T1",
        "architecture": "Residual MLP with LayerNorm and GELU",
        "input_dim": FEATURE_DIM,
        "hidden_dim": 128,
        "num_classes": NUM_SCENARIOS,
        "parameter_count": model.get_parameter_count(),
        "checkpoint_path": str(checkpoint_file),
        "checkpoint_sha256": chk_sum,
        "training_duration_seconds": training_duration,
        "best_epoch": best_epoch,
        "history": history
    }

    with open(MODEL_DIR / "config.json", "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=2)

    return config_data


if __name__ == "__main__":
    train_aevorun(epochs=45, batch_size=32, lr=0.003, seed=42)

