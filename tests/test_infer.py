import pytest

from app import infer


def test_infer_defaults():
    res = infer(23.0, 50.0, 600.0)
    assert isinstance(res, dict)
    assert "action_value" in res
    assert -1.0 <= res["action_value"] <= 1.0


def test_infer_edge_cases():
    # extremes should return valid outputs and not crash
    for t in (0.0, 50.0):
        for h in (0.0, 100.0):
            for c in (0.0, 5000.0):
                r = infer(t, h, c)
                assert "action_label" in r
                assert "comfort_score" in r
