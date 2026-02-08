"""MNEMOS 2.1 - Tests for alert dedup."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

def test_infer_signal_type():
    from alerts.dedup import infer_signal_type, SIGNAL_TYPE_PANIC
    assert infer_signal_type(["Panic selling: -5% drop"]) == SIGNAL_TYPE_PANIC
    assert "overreaction" in infer_signal_type(["Overreaction: 6% in 1d"]).lower()
    assert infer_signal_type([]) == "unknown"

def test_severity_from_score():
    from alerts.dedup import severity_from_score
    assert severity_from_score(0.9) == 4
    assert severity_from_score(0.65) == 2
    assert severity_from_score(0.5) == 1
