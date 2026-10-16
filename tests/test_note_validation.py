import sys
from pathlib import Path

import pandas as pd

# Allow importing the main project module
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from main import validate_note


def test_flooding_note_valid_during_flooding():
    assert validate_note("N001", "Chennai-Bangalore", "2025-03-03") is True


def test_flooding_note_invalid_after_flooding():
    assert validate_note("N001", "Chennai-Bangalore", "2025-03-17") is False


def test_flooding_note_invalid_for_wrong_route():
    assert validate_note("N001", "Mumbai-Pune", "2025-03-03") is False


def test_festival_note_valid_for_correct_route_and_week():
    result = validate_note("N002", "Ahmedabad-Mumbai", "2025-01-20")
    assert result is True


def test_festival_note_invalid_for_wrong_route():
    result = validate_note("N002", "Mumbai-Pune", "2025-01-20")
    assert result is False


def test_festival_note_invalid_for_wrong_week():
    result = validate_note("N002", "Ahmedabad-Mumbai", "2025-02-03")
    assert result is False


def test_diesel_increase_does_not_justify_anomaly():
    assert validate_note("N003", "Mumbai-Pune", "2025-05-05") is False


def test_irrelevant_note_is_rejected():
    assert validate_note("N004", "Delhi-Jaipur", "2024-03-11") is False


def test_unknown_note_is_rejected():
    assert validate_note("N999", "Mumbai-Pune", "2025-01-20") is False
    