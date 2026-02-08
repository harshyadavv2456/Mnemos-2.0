"""MNEMOS 2.1 - Tests for risk governance."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

def test_volatility_filter():
    from risk.governance import volatility_filter
    feats = {"RELIANCE.NS": {"volatility_pct": 5.0}, "TCS.NS": {"volatility_pct": 25.0}}
    out = volatility_filter(feats)
    assert "RELIANCE.NS" in out
    assert "TCS.NS" not in out
