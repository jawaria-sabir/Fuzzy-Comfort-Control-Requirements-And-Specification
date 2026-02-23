import pytest

from app import infer, create_app


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


def test_api_infer_validation_and_success():
    app = create_app({"TESTING": True})
    client = app.test_client()

    # Valid payload
    resp = client.post("/api/infer", json={"temperature": 25, "humidity": 50, "co2": 600})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "ok"
    assert "action_value" in data

    # Invalid payload (wrong types)
    resp2 = client.post("/api/infer", json={"temperature": "hot", "humidity": "wet", "co2": "low"})
    assert resp2.status_code == 400
    data2 = resp2.get_json()
    assert data2["status"] == "error"
