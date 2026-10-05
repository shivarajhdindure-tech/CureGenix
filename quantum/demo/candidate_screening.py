"""
CureGenix candidate screening prototype.

This is a lightweight demonstration layer for the hackathon.
It prepares molecular candidates for quantum analysis.
"""


def get_demo_candidates():
    """
    Return the molecular candidates used in the CureGenix demo.

    These molecules demonstrate the quantum chemistry pipeline;
    they are not being claimed as actual drug candidates.
    """

    return [
        {
            "name": "H2",
            "formula": "H2",
            "description": "Hydrogen molecule - quantum chemistry validation",
        },
        {
            "name": "LiH",
            "formula": "LiH",
            "description": "Lithium hydride - molecular VQE demonstration",
        },
        {
            "name": "H2O",
            "formula": "H2O",
            "description": "Water - chemically meaningful molecular simulation",
        },
    ]