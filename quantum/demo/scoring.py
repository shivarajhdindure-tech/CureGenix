"""
CureGenix quantum candidate scoring.

Prototype ranking layer for the hackathon demo.
This is NOT a validated drug-efficacy prediction.
"""


def calculate_quantum_score(result):
    """
    Convert the quantum-derived molecular energy into
    a normalized prototype ranking score.
    """

    if not result:
        return 0.0

    if result.get("status") != "success":
        return 0.0

    # The formatted result contains the final ground-state energy.
    formatted = result.get("result", {})

    energy = formatted.get("ground_state_energy")

    if energy is None:
        return 0.0

    energy = abs(float(energy))

    # Simple normalized prototype score.
    score = energy / (1.0 + energy)

    return round(score, 4)