from unittest.mock import patch

from backend.mcp.web_mcp import WebMCPServer


def test_generic_fallback_is_explicitly_mock_and_unverified():
    server = WebMCPServer()

    # Force the Wikipedia request to fail, exercising the fallback.
    with patch(
        "backend.mcp.web_mcp.urllib.request.urlopen",
        side_effect=OSError("simulated network failure"),
    ):
        result = server._search_drugs(
            disease="unknown demo target",
            target="unknown demo target",
        )

    compounds = result["known_drugs"]

    assert len(compounds) == 2
    assert all(c["category"] == "mock" for c in compounds)
    assert all(c["verification_status"] == "not_verified" for c in compounds)
    assert all(c["target_association_verified"] is False for c in compounds)
    assert all("Approved Inhibitor" not in c["name"] for c in compounds)
    assert all("Experimental Compound" not in c["name"] for c in compounds)


def test_pubchem_structure_lookup_does_not_claim_drug_approval():
    server = WebMCPServer()

    wikipedia_response = (
        b'{"query":{"pages":{"1":{"extract":"Aspirin"}}}}'
    )
    pubchem_response = (
        b'{"PropertyTable":{"Properties":[{"IsomericSMILES":"CCO"}]}}'
    )

    class FakeResponse:
        def __init__(self, body):
            self.body = body

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return self.body

    def fake_urlopen(request, timeout):
        url = request.full_url
        if "wikipedia.org" in url:
            return FakeResponse(wikipedia_response)
        if "pubchem.ncbi.nlm.nih.gov" in url:
            return FakeResponse(pubchem_response)
        raise AssertionError(f"Unexpected URL: {url}")

    with patch(
        "backend.mcp.web_mcp.urllib.request.urlopen",
        side_effect=fake_urlopen,
    ):
        result = server._search_drugs(
            disease="test",
            target="test",
        )

    compounds = result["known_drugs"]
    assert compounds
    assert all(c["category"] == "unverified" for c in compounds)
    assert all(c["verification_status"] == "structure_lookup_only" for c in compounds)
    assert all(c["target_association_verified"] is False for c in compounds)
