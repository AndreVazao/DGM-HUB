from dgm_hub.core.truth_layer import TruthLayer
from pathlib import Path


def test_truth_layer_basic():
    tl = TruthLayer(str(Path.cwd()))

    snap = tl.create_snapshot()

    assert snap.git_head is not None
    assert len(snap.file_hashes) > 0

    result = tl.verify_snapshot(snap)

    assert result["integrity_ok"] is True
