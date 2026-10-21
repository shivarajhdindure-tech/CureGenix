from backend.mcp.compute_mcp import ComputeMCPServer


def test_toxicity_heuristic_is_deterministic():
    server = ComputeMCPServer()

    first = server._calculate_toxicity("CCO", "Test compound")
    second = server._calculate_toxicity("CCO", "Test compound")

    assert first["toxicity_penalty"] == second["toxicity_penalty"]
    assert first["predicted_toxicity"] == second["predicted_toxicity"]
    assert first["structural_alerts"] == second["structural_alerts"]


def test_toxicity_heuristic_detects_configured_azo_alert():
    server = ComputeMCPServer()

    result = server._calculate_toxicity("CN=NC", "Azo test")

    assert result["alert_count"] == 1
    assert result["toxicity_penalty"] == 0.15
    assert result["predicted_toxicity"] == "low"
    assert any("Azo group" in alert for alert in result["structural_alerts"])


def test_no_detected_alerts_does_not_add_heuristic_penalty():
    server = ComputeMCPServer()

    result = server._calculate_toxicity("CCO", "Ethanol")

    assert result["structural_alerts"] == []
    assert result["alert_count"] == 0
    assert result["toxicity_penalty"] == 0
    assert result["predicted_toxicity"] == "low"
