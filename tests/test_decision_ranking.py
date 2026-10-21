from unittest.mock import patch

from backend.agents.decision_agent import DecisionAgent


class FakeMemory:
    def __init__(self, values):
        self.values = values
        self.stored = {}

    def call_tool(self, tool_name, **kwargs):
        if tool_name == "retrieve":
            key = kwargs["key"]
            return {"data": {"value": self.values.get(key)}}

        if tool_name == "store":
            self.stored[kwargs["key"]] = kwargs["value"]
            return {"data": {"success": True}}

        raise AssertionError(f"Unexpected memory tool: {tool_name}")


def make_candidate(name, category, score):
    return {
        "drug_name": name,
        "smiles": "CCO",
        "category": category,
        "composite_score": score,
        "drug_likeness": 0.7,
        "bbb_permeability": 0.5,
        "potency_proxy": 0.5,
        "toxicity_penalty": 0.1,
        "verification_status": "not_verified",
        "target_association_verified": False,
    }


def run_decision(candidates):
    memory = FakeMemory({
        "screened_molecules": candidates,
        "risk_flags": [],
        "protein_info": {"protein_name": "Test protein"},
        "research_result": {"llm_analysis": ""},
    })
    agent = DecisionAgent({"memory": memory})

    with patch("backend.agents.decision_agent.call_llm", return_value=None):
        result = agent.run({})

    return result, memory


def test_mock_candidate_is_excluded_from_primary_ranking():
    result, memory = run_decision([
        make_candidate("Mock Reference Compound A", "mock", 0.99),
        make_candidate("GEN-TEST01", "novel", 0.70),
    ])

    assert [c["drug_name"] for c in result["recommendations"]] == [
        "GEN-TEST01"
    ]
    assert result["recommendations"][0]["rank"] == 1

    references = result["demonstration_references"]
    assert len(references) == 1
    assert references[0]["drug_name"] == "Mock Reference Compound A"
    assert references[0]["rank"] is None
    assert references[0]["demonstration_only"] is True

    assert result["total_evaluated"] == 2
    assert len(memory.stored["final_decisions"]) == 2
    assert memory.stored["mock_reference_candidates"] == references


def test_all_mock_candidates_produce_empty_primary_ranking():
    result, _ = run_decision([
        make_candidate("Mock Reference Compound A", "mock", 0.99),
        make_candidate("Mock Reference Compound B", "mock", 0.80),
    ])

    assert result["recommendations"] == []
    assert len(result["demonstration_references"]) == 2
    assert result["total_evaluated"] == 2
    assert "Top recommendation: None" in result["summary"]
