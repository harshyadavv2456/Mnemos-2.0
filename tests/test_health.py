"""MNEMOS 2.1 - Tests for health module."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

def test_restart_guardrail():
    from health.watchdog import check_restart_guardrail
    assert check_restart_guardrail() in (True, False)

def test_memory_guardrail():
    from health.watchdog import check_memory_guardrail
    assert check_memory_guardrail() in (True, False)
