from mcp.server.mcpserver import MCPServer
from quantum.mcp.quantum_mcp import (
    get_molecular_info,
    select_active_space,
    run_quantum_vqe,
    run_hamiltonian_simulation,
    run_quantum_qaoa,
)

from quantum.mcp.quantum_mcp import (
    get_molecular_info,
    select_active_space,
    run_quantum_vqe,
)


mcp = MCPServer(
    "CureGenix Quantum MCP",
    version="0.1.0",
)


@mcp.tool()
def molecular_info(
    atom: str,
    basis: str = "sto3g",
    charge: int = 0,
    spin: int = 0,
):
    """
    Get basic molecular information.
    """
    return get_molecular_info(
        atom=atom,
        basis=basis,
        charge=charge,
        spin=spin,
    )


@mcp.tool()
def active_space_selection(
    atom: str,
    num_electrons: int,
    num_spatial_orbitals: int,
    basis: str = "sto3g",
):
    """
    Reduce a molecular electronic structure problem
    to a smaller active space.
    """
    return select_active_space(
        atom=atom,
        num_electrons=num_electrons,
        num_spatial_orbitals=num_spatial_orbitals,
        basis=basis,
    )


@mcp.tool()
def run_vqe(
    atom: str,
    num_electrons: int,
    num_spatial_orbitals: int,
    basis: str = "sto3g",
    maxiter: int = 100,
):
    """
    Run VQE on an active-space molecular Hamiltonian.
    """
    return run_quantum_vqe(
        atom=atom,
        num_electrons=num_electrons,
        num_spatial_orbitals=num_spatial_orbitals,
        basis=basis,
        maxiter=maxiter,
    )

@mcp.tool()
def simulate_hamiltonian(
    atom: str,
    num_electrons: int,
    num_spatial_orbitals: int,
    time: float = 1.0,
    basis: str = "sto3g",
    charge: int = 0,
    spin: int = 0,
):
    """
    Simulate time evolution of a molecular
    active-space Hamiltonian.
    """

    return run_hamiltonian_simulation(
        atom=atom,
        num_electrons=num_electrons,
        num_spatial_orbitals=num_spatial_orbitals,
        time=time,
        basis=basis,
        charge=charge,
        spin=spin,
    )

@mcp.tool()
def run_qaoa(
    num_nodes: int,
    edges: list[list[int]],
    reps: int = 1,
):
    """
    Solve a MaxCut optimization problem using QAOA.
    """

    normalized_edges = [
        (int(edge[0]), int(edge[1]))
        for edge in edges
    ]

    return run_quantum_qaoa(
        num_nodes=num_nodes,
        edges=normalized_edges,
        reps=reps,
    )

if __name__ == "__main__":
    mcp.run()