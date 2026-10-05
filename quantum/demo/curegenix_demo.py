"""
CureGenix Quantum Biotech & Chemistry Demo.

Pipeline:

Candidate Screening
        ↓
Quantum Agent
        ↓
VQE
        ↓
Quantum-derived feature
        ↓
Candidate ranking
"""

import asyncio
from quantum.agent.mcp_client import QuantumMCPClient
from quantum.agent.quantum_agent import QuantumAgent
from quantum.demo.candidate_screening import (
    get_demo_candidates,
)
from quantum.demo.scoring import (
    calculate_quantum_score,
)


async def run_demo():

    print("=" * 70)
    print("                 CUREGENIX QUANTUM MVP")
    print("          Quantum Biotech & Chemistry")
    print("=" * 70)

    candidates = get_demo_candidates()

    print("\nCandidate Screening")
    print("-" * 70)

    for index, candidate in enumerate(
        candidates,
        start=1,
    ):
        print(
            f"{index}. {candidate['name']} "
            f"({candidate['formula']})"
        )
        print(
            f"   {candidate['description']}"
        )

    print("\n" + "=" * 70)
    print("                 QUANTUM ANALYSIS")
    print("=" * 70)

    client = QuantumMCPClient()

    await client.connect()

    agent = QuantumAgent(client)

    results = []

    for candidate in candidates:

        molecule = candidate["formula"]

        print(f"\nAnalyzing {molecule}...")

        request = (
            f"Calculate the lowest energy of {molecule}"
        )

        try:

            result = await agent.run_request(
                request
            )

            score = calculate_quantum_score(
                result
            )

            results.append(
                {
                    "candidate": candidate,
                    "result": result,
                    "quantum_score": score,
                }
            )

            if result.get("status") == "success":

                formatted = result.get(
                    "result",
                    {}
                )

                print(
                    f"  ✓ Quantum analysis completed"
                )

                print(
                    f"  Ground-state energy: "
                    f"{formatted.get('ground_state_energy', 'N/A')} "
                    f"Hartree"
                )

                print(
                    f"  Quantum score: {score}"
                )

            else:

                print(
                    f"  ✗ Quantum analysis failed: "
                    f"{result.get('message', 'Unknown error')}"
                )

        except Exception as exc:

            print(
                f"  ✗ Error analyzing {molecule}: "
                f"{exc}"
            )

    # --------------------------------------------------------
    # Candidate ranking
    # --------------------------------------------------------

    successful_results = [
        item
        for item in results
        if item["quantum_score"] > 0
    ]

    successful_results.sort(
        key=lambda item: item["quantum_score"],
        reverse=True,
    )

    print("\n" + "=" * 70)
    print("                 FINAL QUANTUM RANKING")
    print("=" * 70)

    if not successful_results:

        print("No successful quantum analyses.")

    else:

        print(
            f"{'Rank':<8}"
            f"{'Molecule':<12}"
            f"{'Quantum Score':<15}"
        )

        print("-" * 70)

        for rank, item in enumerate(
            successful_results,
            start=1,
        ):

            print(
                f"{rank:<8}"
                f"{item['candidate']['formula']:<12}"
                f"{item['quantum_score']:<15.4f}"
            )

    print("\n" + "=" * 70)
    print("              QUANTUM ANALYSIS COMPLETE")
    print("=" * 70)

    print(
        "\nNote: Quantum scores shown here are "
        "prototype ranking features for demonstration "
        "and are not validated drug-efficacy predictions."
    )
    await client.close()


def main():
    asyncio.run(run_demo())


if __name__ == "__main__":
    main()