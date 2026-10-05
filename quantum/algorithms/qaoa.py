import numpy as np

from qiskit_algorithms import QAOA
from qiskit_algorithms.optimizers import COBYLA
from qiskit.primitives import StatevectorSampler
from qiskit_optimization import QuadraticProgram
from qiskit_optimization.algorithms import MinimumEigenOptimizer


def build_maxcut_problem(
    num_nodes: int,
    edges: list[tuple[int, int]],
):
    """
    Build a MaxCut optimization problem.

    Each node receives a binary value:
        0 -> partition A
        1 -> partition B

    The objective maximizes the number of edges
    crossing between the two partitions.
    """

    problem = QuadraticProgram("maxcut")

    for i in range(num_nodes):
        problem.binary_var(name=f"x{i}")

    # MaxCut objective:
    #
    # For an edge (i, j), the edge contributes 1
    # when xi != xj.
    #
    # (xi - xj)^2 = xi + xj - 2xi*xj

    linear = {}
    quadratic = {}

    for i, j in edges:
        linear[i] = linear.get(i, 0) + 1
        linear[j] = linear.get(j, 0) + 1

        quadratic[(i, j)] = (
            quadratic.get((i, j), 0) - 2
        )

    problem.maximize(
        linear=linear,
        quadratic=quadratic,
    )

    return problem


def run_qaoa_maxcut(
    num_nodes: int,
    edges: list[tuple[int, int]],
    reps: int = 1,
):
    """
    Solve a MaxCut problem using QAOA.
    """

    problem = build_maxcut_problem(
        num_nodes=num_nodes,
        edges=edges,
    )

    qaoa = QAOA(
        sampler=StatevectorSampler(),
        optimizer=COBYLA(maxiter=100),
        reps=reps,
    )

    optimizer = MinimumEigenOptimizer(qaoa)

    result = optimizer.solve(problem)

    solution = [
        int(round(value))
        for value in result.x
    ]

    # ----------------------------------------------
    # Determine the two partitions
    # ----------------------------------------------

    partition_0 = [
        i for i, value in enumerate(solution)
        if value == 0
    ]

    partition_1 = [
        i for i, value in enumerate(solution)
        if value == 1
    ]

    # ----------------------------------------------
    # Find edges crossing the cut
    # ----------------------------------------------

    cut_edges = []

    for i, j in edges:
        if solution[i] != solution[j]:
            cut_edges.append([i, j])

    return {
        "problem": "MaxCut",

        "num_nodes": num_nodes,

        "edges": [
            list(edge)
            for edge in edges
        ],

        "qaoa_reps": reps,

        "solution": solution,

        "partitions": {
            "partition_0": partition_0,
            "partition_1": partition_1,
        },

        "cut_edges": cut_edges,

        "objective_value": float(
            result.fval
        ),
    }