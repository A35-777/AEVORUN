"""Unit tests for AEVORUN-T1 neural model and checkpoints."""

from pathlib import Path
import numpy as np
import torch
from aevorun.model import AevorunT1Net, AevorunModelWrapper
from aevorun.features import FEATURE_DIM
from aevorun.taxonomy import NUM_SCENARIOS


def test_model_forward():
    net = AevorunT1Net(input_dim=FEATURE_DIM, hidden_dim=128, num_classes=NUM_SCENARIOS)
    x = torch.randn(4, FEATURE_DIM)
    logits = net(x)
    assert logits.shape == (4, NUM_SCENARIOS)

    probs = net.forward_calibrated(x)
    assert probs.shape == (4, NUM_SCENARIOS)
    assert torch.all(probs >= 0.0) and torch.all(probs <= 1.0)


def test_model_parameter_count():
    net = AevorunT1Net()
    params = net.get_parameter_count()
    assert 30000 <= params <= 70000


def test_model_wrapper_checkpoint_io(tmp_path):
    wrapper = AevorunModelWrapper()
    chk_path = tmp_path / "test_model.pt"
    wrapper.save_checkpoint(str(chk_path), metadata={"test": True})
    assert chk_path.exists()

    loaded = AevorunModelWrapper.load_checkpoint(str(chk_path))
    assert loaded.is_fitted is True

    x = np.random.randn(2, FEATURE_DIM).astype(np.float32)
    p1 = wrapper.predict_proba(x)
    p2 = loaded.predict_proba(x)
    np.testing.assert_allclose(p1, p2, atol=1e-5)

