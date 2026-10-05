import asyncio

from quantum.agent.mcp_client import QuantumMCPClient
from quantum.chemistry.molecule_registry import get_molecule

class QuantumAgent:

    def __init__(self, client):
        self.client = client

        self.tools = {
            "vqe": "run_vqe",
            "qaoa": "run_qaoa",
            "active_space": "active_space_selection",
            "hamiltonian": "simulate_hamiltonian",
        }
        self._tool_cache = {}

    async def discover_tools(self):
        tools = await self.client.list_tools()

        self._tool_cache = {
            tool.name: {
                "description": tool.description,
                "input_schema": tool.input_schema,
            }
            for tool in tools
        }

        return self._tool_cache
    
    def get_tool_catalog(self, tools):
        catalog = {}

        for tool_name, info in tools.items():
            schema = info["input_schema"]

            properties = schema.get("properties", {})
            required = schema.get("required", [])

            optional = [
                name
                for name in properties
                if name not in required
            ]

            catalog[tool_name] = {
                "description": info["description"].strip(),
                "required": required,
                "optional": optional,
            }

        return catalog

    def build_tool_arguments(self, tool_name, provided_arguments):
        tools = self._tool_cache

        if tool_name not in tools:
            raise ValueError(
                f"Unknown MCP tool: {tool_name}"
            )

        schema = tools[tool_name]["input_schema"]

        properties = schema.get("properties", {})
        required = schema.get("required", [])

        arguments = {}

        for name in required:
            if name not in provided_arguments:
                raise ValueError(
                    f"Missing required argument '{name}' "
                    f"for tool '{tool_name}'"
                )

            arguments[name] = provided_arguments[name]

        for name in properties:
            if name in provided_arguments:
                arguments[name] = provided_arguments[name]

        return arguments

    async def execute_tool(
        self,
        tool_name,
        provided_arguments,
    ):
        if not self._tool_cache:
            await self.discover_tools()

        arguments = self.build_tool_arguments(
            tool_name,
            provided_arguments,
        )

        result = await self.client.call_tool_json(
            tool_name,
            arguments,
        )

        return result
    
    async def validate_plan(self, plan):
        available_tools = await self.discover_tools()

        missing_tools = [
            tool
            for tool in plan["tools"]
            if tool not in available_tools
        ]

        if missing_tools:
            return {
                "valid": False,
                "missing_tools": missing_tools,
            }

        return {
            "valid": True,
            "missing_tools": [],
        }      

    def choose_workflow(self, request: str):
        request = request.lower()

        if any(keyword in request for keyword in [
            "ground state",
            "ground-state",
            "electronic energy",
            "molecular energy",
            "energy of molecule",
        ]):
            return "molecular_ground_state_energy"

        if any(keyword in request for keyword in [
            "optimization",
            "optimize",
            "maximum cut",
            "maxcut",
            "best combination",
        ]):
            return "optimization"

        if any(keyword in request for keyword in [
            "active space",
            "reduce molecule",
            "reduce molecular",
            "important orbitals",
        ]):
            return "active_space_selection"

        if any(keyword in request for keyword in [
            "simulate dynamics",
            "time evolution",
            "hamiltonian simulation",
            "quantum dynamics",
            "evolution",
        ]):
            return "hamiltonian_simulation"

        return None
        
    def plan(self, request):
        understanding = self.understand_request(request)

        intent = understanding["intent"]

        if intent == "unknown":
            return {
                "status": "error",
                "message": "I could not determine the quantum workflow.",
                "request": request,
            }

        plans = {
            "molecular_ground_state_energy": {
                "workflow": "molecular_ground_state_energy",
                "tools": [
                    "molecular_info",
                    "active_space_selection",
                    "run_vqe",
                ],
            },

            "optimization": {
                "workflow": "optimization",
                "tools": [
                    "run_qaoa",
                ],
            },

            "active_space_selection": {
                "workflow": "active_space_selection",
                "tools": [
                    "active_space_selection",
                ],
            },

            "hamiltonian_simulation": {
                "workflow": "hamiltonian_simulation",
                "tools": [
                    "simulate_hamiltonian",
                ],
            },
        }

        plan = plans[intent].copy()

        plan["status"] = "success"
        plan["intent"] = intent
        plan["method"] = understanding["method"]
        plan["request"] = request

        return plan
    async def execute(
        self,
        request: str,
        **kwargs,
    ):

        plan = self.plan(request)

        if plan.get("status") == "error":
            return plan

        validation = await self.validate_plan(plan)

        if not validation["valid"]:
            return {
                "status": "error",
                "message": "Required MCP tools are unavailable.",
                "workflow": plan["workflow"],
                "missing_tools": validation["missing_tools"],
            }

        workflow = plan["workflow"]

        # ==================================================
        # MOLECULAR GROUND-STATE ENERGY
        # ==================================================

        if workflow == "molecular_ground_state_energy":

            atom = kwargs["atom"]

            num_electrons = kwargs[
                "num_electrons"
            ]

            num_spatial_orbitals = kwargs[
                "num_spatial_orbitals"
            ]

            basis = kwargs.get(
                "basis",
                "sto3g",
            )

            charge = kwargs.get(
                "charge",
                0,
            )

            spin = kwargs.get(
                "spin",
                0,
            )

            maxiter = kwargs.get(
                "maxiter",
                100,
            )

            # Step 1 — molecular information

            molecular_info = (
                await self.client.call_tool_json(
                    "molecular_info",
                    {
                        "atom": atom,
                        "basis": basis,
                        "charge": charge,
                        "spin": spin,
                    },
                )
            )

            # Step 2 — active space

            active_space = (
                await self.client.call_tool_json(
                    "active_space_selection",
                    {
                        "atom": atom,
                        "num_electrons":
                            num_electrons,
                        "num_spatial_orbitals":
                            num_spatial_orbitals,
                        "basis": basis,
                        "charge": charge,
                        "spin": spin,
                    },
                )
            )

            # Step 3 — VQE

            vqe_result = (
                await self.client.call_tool_json(
                    "run_vqe",
                    {
                        "atom": atom,
                        "num_electrons":
                            num_electrons,
                        "num_spatial_orbitals":
                            num_spatial_orbitals,
                        "basis": basis,
                        "charge": charge,
                        "spin": spin,
                        "maxiter": maxiter,
                    },
                )
            )

            return {
                "status": "success",
                "workflow":
                    "molecular_ground_state_energy",
                "selected_workflow": workflow,
                "steps": {
                    "molecular_info":
                        molecular_info,
                    "active_space_selection":
                        active_space,
                    "vqe":
                        vqe_result,
                },
            }

        # ==================================================
        # QAOA
        # ==================================================

        if workflow == "optimization":

            result = (
                await self.client.call_tool_json(
                    "run_qaoa",
                    {
                        "num_nodes":
                            kwargs["num_nodes"],
                        "edges":
                            kwargs["edges"],
                        "reps":
                            kwargs.get(
                                "reps",
                                1,
                            ),
                    },
                )
            )

            return {
                "status": "success",
                "workflow": "optimization",
                "selected_workflow": workflow,
                "result": result,
            }

        # ==================================================
        # ACTIVE SPACE
        # ==================================================

        if workflow == "active_space_selection":

            result = (
                await self.client.call_tool_json(
                    "active_space_selection",
                    {
                        "atom":
                            kwargs["atom"],
                        "num_electrons":
                            kwargs[
                                "num_electrons"
                            ],
                        "num_spatial_orbitals":
                            kwargs[
                                "num_spatial_orbitals"
                            ],
                        "basis":
                            kwargs.get(
                                "basis",
                                "sto3g",
                            ),
                        "charge":
                            kwargs.get(
                                "charge",
                                0,
                            ),
                        "spin":
                            kwargs.get(
                                "spin",
                                0,
                            ),
                    },
                )
            )

            return {
                "status": "success",
                "workflow":
                    "active_space_selection",
                "selected_workflow": workflow,
                "result": result,
            }

        # ==================================================
        # HAMILTONIAN SIMULATION
        # ==================================================

        if workflow == "hamiltonian_simulation":

            result = (
                await self.client.call_tool_json(
                    "simulate_hamiltonian",
                    {
                        "atom":
                            kwargs["atom"],
                        "num_electrons":
                            kwargs[
                                "num_electrons"
                            ],
                        "num_spatial_orbitals":
                            kwargs[
                                "num_spatial_orbitals"
                            ],
                        "time":
                            kwargs.get(
                                "time",
                                1.0,
                            ),
                        "basis":
                            kwargs.get(
                                "basis",
                                "sto3g",
                            ),
                        "charge":
                            kwargs.get(
                                "charge",
                                0,
                            ),
                        "spin":
                            kwargs.get(
                                "spin",
                                0,
                            ),
                    },
                )
            )

            return {
                "status": "success",
                "workflow":
                    "hamiltonian_simulation",
                "selected_workflow": workflow,
                "result": result,
            }

        return {
            "status": "error",
            "message": f"Unsupported workflow: {workflow}"
        }
    
    def format_result(self, result, molecule_name=None):

        # ============================================================
        # ERROR
        # ============================================================

        if result.get("status") == "error":
            return result

        # ============================================================
        # VQE
        # ============================================================

        if "vqe_result" in result:

            vqe = result["vqe_result"]

            energy = vqe["energy"]
            active_space = vqe["active_space"]
            hamiltonian = vqe["hamiltonian"]
            vqe_info = vqe["vqe"]

            selection_method = result.get(
                "active_space_plan", {}
            ).get("selection_method")

            return {
                "status": "success",
                "analysis": "Quantum Analysis Complete",
                "molecule": molecule_name or vqe["molecule"],
                "method": "VQE",
                "basis": vqe["basis"],

                "active_space": {
                    "electrons": active_space["electrons"],
                    "spatial_orbitals": active_space["spatial_orbitals"],
                    "selected_orbitals": active_space.get(
                        "selected_orbitals"
                    ),
                    "selection_method": selection_method,
                },

                "hamiltonian": {
                    "qubits": hamiltonian["qubits"],
                    "pauli_terms": hamiltonian["pauli_terms"],
                },

                # ----------------------------------------------------
                # Detailed chemistry-aware energy information
                # ----------------------------------------------------

                "energy_analysis": {
                    "raw_active_space_energy": round(
                        energy.get(
                            "raw_active_space_energy",
                            0.0
                        ),
                        6,
                    ),

                    "active_space_correction": round(
                        energy.get(
                            "active_space_correction",
                            0.0
                        ),
                        6,
                    ),

                    "electronic_energy": round(
                        energy.get(
                            "electronic_energy",
                            0.0
                        ),
                        6,
                    ),

                    "nuclear_repulsion_energy": round(
                        energy.get(
                            "nuclear_repulsion_energy",
                            0.0
                        ),
                        6,
                    ),

                    "total_molecular_energy": round(
                        energy.get(
                            "total_molecular_energy",
                            0.0
                        ),
                        6,
                    ),
                },

                # Keep this for backward compatibility
                "ground_state_energy": round(
                    energy.get(
                        "total_molecular_energy",
                        0.0
                    ),
                    6,
                ),

                "energy_unit": "Hartree",

                "optimizer": vqe_info["optimizer"],

                "max_iterations": vqe_info[
                    "max_iterations"
                ],
            }

        # ============================================================
        # QAOA
        # ============================================================

        if result.get("problem") == "MaxCut":

            return {
                "status": "success",
                "analysis": "Quantum Optimization Complete",
                "method": "QAOA",
                "problem": result["problem"],
                "num_nodes": result["num_nodes"],
                "solution": result["solution"],
                "partitions": result["partitions"],
                "cut_edges": result["cut_edges"],
                "objective_value": result["objective_value"],
            }

        # ============================================================
        # HAMILTONIAN SIMULATION
        # ============================================================

        if "simulation" in result:

            simulation = result["simulation"]

            return {
                "status": "success",
                "analysis": "Hamiltonian Simulation Complete",
                "method": "Hamiltonian Simulation",

                "molecule": molecule_name or result.get(
                    "molecule"
                ),

                "basis": result.get("basis"),

                "active_space": result.get(
                    "active_space"
                ),

                "num_qubits": result.get(
                    "hamiltonian",
                    {}
                ).get("qubits"),

                "time": simulation.get("time"),

                "probabilities": simulation.get(
                    "probabilities",
                    {}
                ),
            }

        # ============================================================
        # ACTIVE SPACE SELECTION
        # ============================================================

        if "active_space" in result:

            active_space = result["active_space"]

            return {
                "status": "success",
                "analysis": "Active Space Selection Complete",
                "method": "Active Space",

                "molecule": molecule_name or result.get(
                    "molecule"
                ),

                "basis": result.get("basis"),

                "active_space": active_space,
            }

        # ============================================================
        # FALLBACK
        # ============================================================

        return result

    async def get_molecular_info(
        self,
        atom,
        basis="sto3g",
        charge=0,
        spin=0,
    ):
        return await self.execute_tool(
            "molecular_info",
            {
                "atom": atom,
                "basis": basis,
                "charge": charge,
                "spin": spin,
            },
        )

    def select_homo_lumo_space(self, molecular_info):
        """
        Select a small active space around the HOMO/LUMO region.

        This function only analyzes the molecular information.
        It does not modify or execute the VQE workflow.
        """

        num_particles = molecular_info["num_particles"]
        orbital_energies = molecular_info.get("orbital_energies", [])
        orbital_occupations = molecular_info.get(
            "orbital_occupations", []
        )

        if not orbital_energies:
            raise ValueError(
                "Orbital energies are not available."
            )

        if not orbital_occupations:
            raise ValueError(
                "Orbital occupations are not available."
            )

        if len(orbital_energies) != len(orbital_occupations):
            raise ValueError(
                "Orbital energies and occupations "
                "must have the same length."
            )

        # ------------------------------------------------------------
        # Identify occupied and virtual orbitals
        # ------------------------------------------------------------

        occupied = [
            i
            for i, occupation in enumerate(orbital_occupations)
            if occupation > 0
        ]

        virtual = [
            i
            for i, occupation in enumerate(orbital_occupations)
            if occupation == 0
        ]

        if not occupied:
            raise ValueError(
                "No occupied molecular orbitals were found."
            )

        # HOMO = highest-energy occupied orbital
        homo = max(
            occupied,
            key=lambda i: orbital_energies[i],
        )

        # LUMO = lowest-energy virtual orbital
        lumo = None

        if virtual:
            lumo = min(
                virtual,
                key=lambda i: orbital_energies[i],
            )

        # ------------------------------------------------------------
        # Select HOMO + LUMO
        # ------------------------------------------------------------

        selected_orbitals = [homo]

        if lumo is not None and lumo != homo:
            selected_orbitals.append(lumo)

        selected_orbitals.sort()

        # ------------------------------------------------------------
        # Conservative electron selection
        #
        # Preserve the closed-shell electron count represented
        # by the selected occupied orbital(s).
        # ------------------------------------------------------------

        total_alpha = num_particles[0]
        total_beta = num_particles[1]

        occupied_selected = [
            orbital
            for orbital in selected_orbitals
            if orbital in occupied
        ]

        if not occupied_selected:
            raise ValueError(
                "Selected active space contains no occupied orbital."
            )

        active_alpha = min(
            len(occupied_selected),
            total_alpha,
        )

        active_beta = min(
            len(occupied_selected),
            total_beta,
        )

        return {
            "selected_orbitals": selected_orbitals,
            "homo": homo,
            "lumo": lumo,
            "homo_energy": float(
                orbital_energies[homo]
            ),
            "lumo_energy": (
                float(orbital_energies[lumo])
                if lumo is not None
                else None
            ),
            "num_spatial_orbitals": len(
                selected_orbitals
            ),
            "num_electrons": (
                active_alpha + active_beta
            ),
            "num_particles": [
                active_alpha,
                active_beta,
            ],
        }

    def test_homo_lumo_active_space(self, atom="Li 0 0 0; H 0 0 1.6"):
        """
        Temporary diagnostic:
        verify HOMO/LUMO selection against Qiskit Nature's
        active-space construction.
        """

        molecular_info = self.get_molecular_info_sync(
            atom=atom,
            basis="sto3g",
        )

        selection = self.select_homo_lumo_space(
            molecular_info
        )

        return selection

    def choose_active_space(
        self,
        molecular_info,
        active_electrons=None,
        active_spatial_orbitals=None,
    ):
        """
        Choose an active space using molecular orbital
        energies and occupations.

        Automatic strategy:
            1. Identify occupied orbitals.
            2. Identify virtual orbitals.
            3. Find HOMO.
            4. Find LUMO.
            5. Select the HOMO/LUMO region.
            6. Determine the active electron count.
            7. Validate the active space.
        """

        num_particles = molecular_info["num_particles"]

        total_electrons = sum(num_particles)
        total_orbitals = molecular_info["num_spatial_orbitals"]

        orbital_energies = molecular_info.get(
            "orbital_energies",
            [],
        )

        orbital_occupations = molecular_info.get(
            "orbital_occupations",
            [],
        )

        # ============================================================
        # 1. USER-DEFINED ACTIVE SPACE
        # ============================================================

        user_selected = (
            active_electrons is not None
            or active_spatial_orbitals is not None
        )

        if user_selected:

            if active_electrons is None:
                active_electrons = 2

            if active_spatial_orbitals is None:
                active_spatial_orbitals = 2

            selected_orbitals = None

            selection_method = "user_defined"

        # ============================================================
        # 2. AUTOMATIC ORBITAL-AWARE SELECTION
        # ============================================================

        else:

            selection_method = "automatic_homo_lumo"

            if (
                not orbital_energies
                or not orbital_occupations
            ):

                # Safe fallback
                active_electrons = min(
                    2,
                    total_electrons,
                )

                active_spatial_orbitals = min(
                    2,
                    total_orbitals,
                )

                selected_orbitals = None

                selection_method = (
                    "automatic_fallback"
                )

            else:

                # ----------------------------------------------------
                # Identify occupied and virtual orbitals
                # ----------------------------------------------------

                occupied_orbitals = [
                    i
                    for i, occupation
                    in enumerate(orbital_occupations)
                    if occupation > 0
                ]

                virtual_orbitals = [
                    i
                    for i, occupation
                    in enumerate(orbital_occupations)
                    if occupation == 0
                ]

                # ----------------------------------------------------
                # Small molecule
                # ----------------------------------------------------

                if total_orbitals <= 2:

                    active_spatial_orbitals = (
                        total_orbitals
                    )

                    active_electrons = (
                        total_electrons
                    )

                    selected_orbitals = list(
                        range(total_orbitals)
                    )

                    selection_method = (
                        "all_orbitals_small_molecule"
                    )

                # ----------------------------------------------------
                # Larger molecule
                # ----------------------------------------------------

                else:

                    if not occupied_orbitals:

                        raise ValueError(
                            "No occupied molecular "
                            "orbitals were found."
                        )

                    # ------------------------------------------------
                    # HOMO
                    # ------------------------------------------------

                    homo = max(
                        occupied_orbitals,
                        key=lambda i:
                        orbital_energies[i],
                    )

                    # ------------------------------------------------
                    # LUMO
                    # ------------------------------------------------

                    if virtual_orbitals:

                        lumo = min(
                            virtual_orbitals,
                            key=lambda i:
                            orbital_energies[i],
                        )

                    else:

                        lumo = None

                    # ------------------------------------------------
                    # Select HOMO + LUMO
                    # ------------------------------------------------

                    selected_orbitals = [homo]

                    if (
                        lumo is not None
                        and lumo != homo
                    ):
                        selected_orbitals.append(lumo)

                    selected_orbitals.sort()

                    # ------------------------------------------------
                    # Active orbital count
                    # ------------------------------------------------

                    active_spatial_orbitals = len(
                        selected_orbitals
                    )

                    # ------------------------------------------------
                    # Active electron count
                    # ------------------------------------------------

                    occupied_selected = [
                        orbital
                        for orbital
                        in selected_orbitals
                        if orbital
                        in occupied_orbitals
                    ]

                    active_electrons = min(
                        2 * len(
                            occupied_selected
                        ),
                        total_electrons,
                    )

                    # Safety fallback
                    if active_electrons == 0:

                        active_electrons = min(
                            2,
                            total_electrons,
                        )

        # ============================================================
        # 3. VALIDATION
        # ============================================================

        if active_electrons <= 0:

            raise ValueError(
                "Active electrons must be greater than zero."
            )

        if active_electrons > total_electrons:

            raise ValueError(
                "Active electrons cannot exceed "
                "total molecular electrons."
            )

        if active_spatial_orbitals <= 0:

            raise ValueError(
                "Active spatial orbitals must be "
                "greater than zero."
            )

        if active_spatial_orbitals > total_orbitals:

            raise ValueError(
                "Active orbitals cannot exceed "
                "total spatial orbitals."
            )

        if active_electrons > (
            2 * active_spatial_orbitals
        ):

            raise ValueError(
                "Active electrons cannot exceed "
                "the capacity of the selected "
                "active orbitals."
            )

        # ============================================================
        # 4. RETURN ACTIVE-SPACE PLAN
        # ============================================================

        return {
            "num_electrons": active_electrons,

            "num_spatial_orbitals": (
                active_spatial_orbitals
            ),

            "selected_orbitals": (
                selected_orbitals
            ),

            "original_electrons": (
                total_electrons
            ),

            "original_spatial_orbitals": (
                total_orbitals
            ),

            "selection_method": (
                selection_method
            ),
        }
    
    async def run_molecular_workflow(
        self,
        atom,
        basis="sto3g",
        active_electrons=None,
        active_spatial_orbitals=None,
        maxiter=50,
    ):
        # Step 1: Get molecular information
        molecular_info = await self.get_molecular_info(
            atom=atom,
            basis=basis,
        )

        # Step 2: Choose active space
        active_space = self.choose_active_space(
            molecular_info=molecular_info,
            active_electrons=active_electrons,
            active_spatial_orbitals=active_spatial_orbitals,
        )

        # Step 3: Validate active space through MCP
        active_space_result = await self.execute_tool(
            "active_space_selection",
            {
                "atom": atom,
                "num_electrons": active_space["num_electrons"],
                "num_spatial_orbitals": active_space[
                    "num_spatial_orbitals"
                ],
                "basis": basis,
                "active_orbitals": active_space.get(
                    "selected_orbitals"
                ),
            },
        )

        # Step 4: Run VQE through MCP
        vqe_result = await self.execute_tool(
            "run_vqe",
            {
                "atom": atom,
                "num_electrons": active_space["num_electrons"],
                "num_spatial_orbitals": active_space[
                    "num_spatial_orbitals"
                ],
                "basis": basis,
                "maxiter": maxiter,
                "active_orbitals": active_space.get(
                    "selected_orbitals"
                ),
            },
        )

        vqe_result["active_space"]["selected_orbitals"] = (
            active_space.get("selected_orbitals")
        )

        return {
            "molecular_info": molecular_info,
            "active_space_plan": active_space,
            "active_space_result": active_space_result,
            "vqe_result": vqe_result,
        }

    def understand_request(self, request):
        """
        Understand the user's natural-language quantum request.

        The method identifies the scientific intent and maps it
        to the corresponding quantum workflow.
        """

        text = request.lower().strip()

        # ------------------------------------------------------------
        # Molecular ground-state energy
        # ------------------------------------------------------------

        ground_state_keywords = [
            "ground state",
            "ground-state",
            "groundstate",
            "lowest energy",
            "minimum energy",
            "lowest-energy",
            "molecular energy",
        ]

        if any(
            keyword in text
            for keyword in ground_state_keywords
        ):
            return {
                "intent": "molecular_ground_state_energy",
                "method": "VQE",
                "workflow": "molecular_ground_state_energy",
                "confidence": 0.95,
            }

        # ------------------------------------------------------------
        # Hamiltonian simulation
        # ------------------------------------------------------------

        simulation_keywords = [
            "simulate",
            "simulation",
            "time evolution",
            "time-evolution",
            "evolve",
            "evolution",
        ]

        if any(
            keyword in text
            for keyword in simulation_keywords
        ):
            return {
                "intent": "hamiltonian_simulation",
                "method": "Hamiltonian Simulation",
                "workflow": "hamiltonian_simulation",
                "confidence": 0.95,
            }

        # ------------------------------------------------------------
        # Active-space selection
        # ------------------------------------------------------------

        active_space_keywords = [
            "active space",
            "active-space",
            "active orbital",
            "active orbitals",
            "homo lumo",
            "homo/lumo",
        ]

        if any(
            keyword in text
            for keyword in active_space_keywords
        ):
            return {
                "intent": "active_space_selection",
                "method": "Active Space",
                "workflow": "active_space_selection",
                "confidence": 0.95,
            }

        # ------------------------------------------------------------
        # Optimization / QAOA
        # ------------------------------------------------------------

        optimization_keywords = [
            "qaoa",
            "optimization",
            "optimisation",
            "optimize",
            "optimise",
            "maximum cut",
            "maxcut",
            "qubo",
        ]

        if any(
            keyword in text
            for keyword in optimization_keywords
        ):
            return {
                "intent": "optimization",
                "method": "QAOA",
                "workflow": "optimization",
                "confidence": 0.95,
            }

        # ------------------------------------------------------------
        # Unknown request
        # ------------------------------------------------------------

        return {
            "intent": "unknown",
            "method": None,
            "workflow": None,
            "confidence": 0.0,
        }

    def extract_request_parameters(self, request, understanding=None):
        """
        Extract scientific and algorithm parameters from a
        natural-language quantum request.
        """

        import re

        if understanding is None:
            understanding = self.understand_request(request)

        request_lower = request.lower().strip()

        params = {
            "basis": "sto3g",
            "charge": 0,
            "spin": 0,
        }

        # ---------------------------------------------------------
        # Molecule detection
        # ---------------------------------------------------------

        molecule_aliases = {
            # Longer / more specific molecules first
            "water": "H2O",
            "h2o": "H2O",

            "hydrogen molecule": "H2",
            "h2": "H2",
            "hydrogen": "H2",

            "lithium hydride": "LiH",
            "lithium-hydride": "LiH",
            "lih": "LiH",

            "helium hydride ion": "HeH+",
            "helium hydride": "HeH+",
            "heh+": "HeH+",
            "heh +": "HeH+",
            "heh": "HeH+",
        }

        molecule = None

        # Check longer aliases first
        for name in sorted(
            molecule_aliases,
            key=len,
            reverse=True,
        ):
            # Use word boundaries for chemical formulas
            if re.search(
                rf"(?<![a-zA-Z0-9]){re.escape(name)}(?![a-zA-Z0-9])",
                request_lower,
            ):
                molecule = molecule_aliases[name]
                break

        if molecule is not None:
            params["molecule"] = molecule

        # ---------------------------------------------------------
        # Default molecular geometries
        # ---------------------------------------------------------

        geometries = {
            "H2": "H 0 0 0; H 0 0 0.735",

            "LiH": "Li 0 0 0; H 0 0 1.6",

            "HeH+": "He 0 0 0; H 0 0 0.77",

            "H2O": "O 0 0 0; H 0 0.757 0.586; H 0 -0.757 0.586",
        }

        if molecule in geometries:
            params["atom"] = geometries[molecule]

        # ---------------------------------------------------------
        # Explicit molecular geometry
        # ---------------------------------------------------------

        geometry_match = re.search(
            r"((?:[A-Z][a-z]?\s+"
            r"-?\d+(?:\.\d+)?\s+"
            r"-?\d+(?:\.\d+)?\s+"
            r"-?\d+(?:\.\d+)?"
            r"(?:\s*;\s*|,\s*))+"
            r"[A-Z][a-z]?\s+"
            r"-?\d+(?:\.\d+)?\s+"
            r"-?\d+(?:\.\d+)?\s+"
            r"-?\d+(?:\.\d+)?)",
            request,
        )

        if geometry_match:
            params["atom"] = geometry_match.group(1)

        # ---------------------------------------------------------
        # Basis set detection
        # ---------------------------------------------------------

        basis_patterns = [
            ("sto-3g", "sto3g"),
            ("sto3g", "sto3g"),
            ("6-31g*", "631g*"),
            ("6-31g", "631g"),
            ("cc-pvdz", "ccpvdz"),
            ("cc-pvtz", "ccpvtz"),
        ]

        for pattern, canonical_basis in basis_patterns:
            if pattern in request_lower:
                params["basis"] = canonical_basis
                break

        # ---------------------------------------------------------
        # Charge detection
        # ---------------------------------------------------------

        charge_patterns = [
            r"(?:charge|charged)\s*(?:is|=|:)?\s*(-?\d+)",
            r"(?:charge)\s+(-?\d+)",
        ]

        for pattern in charge_patterns:
            charge_match = re.search(
                pattern,
                request_lower,
            )

            if charge_match:
                params["charge"] = int(
                    charge_match.group(1)
                )
                break

        # ---------------------------------------------------------
        # Spin / multiplicity detection
        # ---------------------------------------------------------

        spin_patterns = [
            r"(?:spin)\s*(?:is|=|:)?\s*(-?\d+)",
            r"(?:multiplicity)\s*(?:is|=|:)?\s*(\d+)",
        ]

        for pattern in spin_patterns:
            spin_match = re.search(
                pattern,
                request_lower,
            )

            if spin_match:
                params["spin"] = int(
                    spin_match.group(1)
                )
                break

        # ---------------------------------------------------------
        # QAOA parameters
        # ---------------------------------------------------------

        if understanding["intent"] == "optimization":

            params["reps"] = 1

            # Example:
            # "3 node MaxCut"
            # "5 nodes"
            nodes_match = re.search(
                r"(\d+)\s*[- ]?\s*nodes?",
                request_lower,
            )

            if nodes_match:
                params["num_nodes"] = int(
                    nodes_match.group(1)
                )

            # Example:
            # "reps = 2"
            # "2 repetitions"
            # "3 layers"
            reps_match = re.search(
                r"(?:reps?|repetitions?|layers?)"
                r"\s*(?:is|=|:)?\s*(\d+)",
                request_lower,
            )

            if reps_match:
                params["reps"] = int(
                    reps_match.group(1)
                )

            # Default graph for 3-node MaxCut
            if params.get("num_nodes") == 3:
                params["edges"] = [
                    [0, 1],
                    [1, 2],
                    [0, 2],
                ]

        # ---------------------------------------------------------
        # Hamiltonian simulation parameters
        # ---------------------------------------------------------

        if understanding["intent"] == "hamiltonian_simulation":

            # Default simulation time
            params["time"] = 1.0

            # Examples:
            # "time = 2"
            # "time 0.5"
            # "t = 1.5"
            # "for 2 seconds"
            # "for 0.5 seconds"
            # "2 seconds"
            # "2 sec"

            time_patterns = [
                # time = 2
                r"(?:time|t)\s*(?:is|=|:)?\s*(\d+(?:\.\d+)?)",

                # for 2 seconds / for 0.5 seconds
                r"(?:for)\s+(\d+(?:\.\d+)?)\s*(?:seconds?|secs?|s)\b",

                # 2 seconds / 0.5 seconds
                r"\b(\d+(?:\.\d+)?)\s*(?:seconds?|secs?)\b",
            ]

            for pattern in time_patterns:
                time_match = re.search(
                    pattern,
                    request_lower,
                )

                if time_match:
                    params["time"] = float(
                        time_match.group(1)
                    )
                    break

        # ---------------------------------------------------------
        # Active-space parameters
        # ---------------------------------------------------------

        if understanding["intent"] == "active_space_selection":

            params["num_electrons"] = 2
            params["num_spatial_orbitals"] = 2

            params["use_homo_lumo"] = (
                "homo" in request_lower
                or "lumo" in request_lower
            )

            electrons_match = re.search(
                r"(?:electrons?|e)"
                r"\s*(?:is|=|:)?\s*(\d+)",
                request_lower,
            )

            orbitals_match = re.search(
                r"(?:spatial\s+orbitals?|orbitals?|o)"
                r"\s*(?:is|=|:)?\s*(\d+)",
                request_lower,
            )

            if electrons_match:
                params["num_electrons"] = int(
                    electrons_match.group(1)
                )

            if orbitals_match:
                params["num_spatial_orbitals"] = int(
                    orbitals_match.group(1)
                )

        # ---------------------------------------------------------
        # VQE parameters
        # ---------------------------------------------------------
        # VQE
        if understanding["intent"] == "molecular_ground_state_energy":
            params["maxiter"] = 50

            electrons_match = re.search(
                r"\b(\d+)\s*electrons?\b",
                request_lower,
            )

            orbitals_match = re.search(
                r"\b(\d+)\s*(?:spatial\s+)?orbitals?\b",
                request_lower,
            )

            maxiter_match = re.search(
                r"(?:maxiter|max\s*iterations?|iterations?)"
                r"\s*(?:is|=|:)?\s*(\d+)",
                request_lower,
            )

            if electrons_match:
                params["num_electrons"] = int(
                    electrons_match.group(1)
                )

            if orbitals_match:
                params["num_spatial_orbitals"] = int(
                    orbitals_match.group(1)
                )

            if maxiter_match:
                params["maxiter"] = int(
                    maxiter_match.group(1)
                )

        return params

    async def execute_plan(self, plan, parameters):
        """
        Execute the workflow selected by the agent's plan.
        """

        workflow = plan["workflow"]

        # ================================================================
        # MOLECULAR GROUND-STATE ENERGY → VQE
        # ================================================================
        if workflow == "molecular_ground_state_energy":

            return await self.run_molecular_workflow(
                atom=parameters["atom"],
                basis=parameters.get("basis", "sto3g"),
                active_electrons=parameters.get(
                    "num_electrons",
                ),
                active_spatial_orbitals=parameters.get(
                    "num_spatial_orbitals",
                ),
                maxiter=parameters.get(
                    "maxiter",
                    50,
                ),
            )

        # ================================================================
        # QAOA OPTIMIZATION
        # ================================================================
        if workflow == "optimization":

            return await self.execute_tool(
                "run_qaoa",
                {
                    "num_nodes": parameters.get("num_nodes", 3),
                    "edges": parameters.get(
                        "edges",
                        [[0, 1], [1, 2], [0, 2]],
                    ),
                    "reps": parameters.get("reps", 1),
                },
            )

        # ================================================================
        # ACTIVE SPACE SELECTION
        # ================================================================
        if workflow == "active_space_selection":

            # ---------------------------------------------------------
            # Get molecular information first
            # ---------------------------------------------------------

            molecular_info = await self.get_molecular_info(
                atom=parameters["atom"],
                basis=parameters.get("basis", "sto3g"),
                charge=parameters.get("charge", 0),
                spin=parameters.get("spin", 0),
            )

            # ---------------------------------------------------------
            # Automatically select the active space
            # using HOMO/LUMO information
            # ---------------------------------------------------------

            # ---------------------------------------------------------
            # Determine whether the user explicitly requested
            # an active-space size or wants HOMO/LUMO selection
            # ---------------------------------------------------------

            if parameters.get("use_homo_lumo", False):

                active_space = self.choose_active_space(
                    molecular_info=molecular_info,
                    active_electrons=None,
                    active_spatial_orbitals=None,
                )

            else:

                active_space = self.choose_active_space(
                    molecular_info=molecular_info,
                    active_electrons=parameters.get(
                        "num_electrons"
                    ),
                    active_spatial_orbitals=parameters.get(
                        "num_spatial_orbitals"
                    ),
                )

            # ---------------------------------------------------------
            # Apply the selected active space
            # ---------------------------------------------------------

            result = await self.execute_tool(
                "active_space_selection",
                {
                    "atom": parameters["atom"],
                    "num_electrons": active_space["num_electrons"],
                    "num_spatial_orbitals": active_space[
                        "num_spatial_orbitals"
                    ],
                    "basis": parameters.get("basis", "sto3g"),
                    "charge": parameters.get("charge", 0),
                    "spin": parameters.get("spin", 0),
                    "active_orbitals": active_space.get(
                        "selected_orbitals"
                    ),
                },
            )

            # ---------------------------------------------------------
            # Add agent's selection information to the result
            # ---------------------------------------------------------

            result["selected_orbitals"] = active_space.get(
                "selected_orbitals"
            )

            result["selection_method"] = active_space.get(
                "selection_method"
            )

            result["active_electrons"] = active_space[
                "num_electrons"
            ]

            result["active_spatial_orbitals"] = active_space[
                "num_spatial_orbitals"
            ]

            return result

        # ================================================================
        # HAMILTONIAN SIMULATION
        # ================================================================
        if workflow == "hamiltonian_simulation":

            return await self.execute_tool(
                "simulate_hamiltonian",
                {
                    "atom": parameters["atom"],
                    "basis": parameters.get("basis", "sto3g"),
                    "charge": parameters.get("charge", 0),
                    "spin": parameters.get("spin", 0),
                    "num_electrons": parameters.get(
                        "num_electrons",
                        2,
                    ),
                    "num_spatial_orbitals": parameters.get(
                        "num_spatial_orbitals",
                        2,
                    ),
                    "time": parameters.get(
                        "time",
                        1.0,
                    ),
                },
            )

        # ================================================================
        # UNKNOWN WORKFLOW
        # ================================================================
        return {
            "status": "error",
            "message": f"Unsupported workflow: {workflow}",
        }

    async def run_request(self, request):
        """
        Main entry point for processing a natural-language quantum request.

        Flow:
            1. Understand request
            2. Create workflow plan
            3. Validate required MCP tools
            4. Extract parameters
            5. Validate basic parameters
            6. Execute the planned workflow
            7. Format and return the result
        """

        # ============================================================
        # 1. UNDERSTAND THE REQUEST
        # ============================================================

        understanding = self.understand_request(request)

        # ============================================================
        # 2. CREATE WORKFLOW PLAN
        # ============================================================

        plan = self.plan(request)

        if plan.get("status") == "error":
            return plan

        # ============================================================
        # 3. VALIDATE WORKFLOW TOOLS
        # ============================================================

        validation = await self.validate_plan(plan)

        if not validation["valid"]:
            return {
                "status": "error",
                "message": "Workflow requires unavailable quantum tools.",
                "missing_tools": validation["missing_tools"],
                "workflow": plan["workflow"],
            }

        # ============================================================
        # 4. DISPLAY WORKFLOW PLAN
        # ============================================================

        print("\n" + "=" * 70)
        print("                         WORKFLOW PLAN")
        print("=" * 70)

        print(f"Intent:  {plan['intent']}")
        print(f"Method:  {plan['method']}")
        print(f"Workflow: {plan['workflow']}")

        print("\nTools:")

        for i, tool in enumerate(plan["tools"], start=1):
            print(f"  {i}. {tool}")

        print("=" * 70)

        # ============================================================
        # 5. EXTRACT PARAMETERS
        # ============================================================

        parameters = self.extract_request_parameters(
            request,
            understanding,
        )

        # ============================================================
        # 6. BASIC VALIDATION
        # ============================================================

        intent = understanding["intent"]

        # Workflows involving molecules require an atom specification.
        if intent in {
            "molecular_ground_state_energy",
            "hamiltonian_simulation",
            "active_space_selection",
        }:

            if parameters.get("atom") is None:
                return {
                    "status": "error",
                    "message": "I could not identify the molecule.",
                }

        # ============================================================
        # 7. EXECUTE THE PLAN
        # ============================================================

        try:

            raw_result = await self.execute_plan(
                plan,
                parameters,
            )

        except Exception as e:

            return {
                "status": "error",
                "message": f"Workflow execution failed: {str(e)}",
                "workflow": plan["workflow"],
            }

        # ============================================================
        # 8. CHECK FOR TOOL ERROR
        # ============================================================

        if isinstance(raw_result, dict):

            if raw_result.get("status") == "error":
                return raw_result

        # ============================================================
        # 9. FORMAT RESULT
        # ============================================================

        molecule_name = parameters.get("molecule")

        formatted_result = self.format_result(
            raw_result,
            molecule_name=molecule_name,
        )

        # ============================================================
        # 10. RETURN FINAL RESPONSE
        # ============================================================

        return {
            "status": "success",
            "request": request,
            "understanding": understanding,
            "plan": {
                "intent": plan["intent"],
                "method": plan["method"],
                "workflow": plan["workflow"],
                "tools": plan["tools"],
            },
            "parameters": parameters,
            "result": formatted_result,
            "raw_result": raw_result,
        }
    

async def main():

    print("=" * 70)
    print("              CUREGENIX QUANTUM AGENT")
    print("=" * 70)

    request = input("\nEnter your request: ").strip()

    if not request:
        print("No request provided.")
        return

    client = QuantumMCPClient()

    try:
        # =========================================================
        # CONNECT TO MCP SERVER
        # =========================================================

        await client.connect()

        # Create agent with MCP client
        agent = QuantumAgent(client)

        # =========================================================
        # PROCESS USER REQUEST
        # =========================================================

        result = await agent.run_request(request)

        # =========================================================
        # CHECK FOR ERROR
        # =========================================================

        if result["status"] != "success":

            print()
            print("=" * 70)
            print("                         ERROR")
            print("=" * 70)

            print()
            print(
                result.get(
                    "message",
                    "Unknown error occurred."
                )
            )

            return

        # =========================================================
        # GET FORMATTED RESULT
        # =========================================================

        formatted = result["result"]

        # =========================================================
        # VQE
        # =========================================================

        if formatted.get("method") == "VQE":

            print()
            print("=" * 70)
            print("                         VQE RESULT")
            print("=" * 70)

            print()
            print(f"Method:   {formatted['method']}")
            print(f"Molecule: {formatted['molecule']}")
            print(f"Basis:    {formatted['basis']}")

            # -----------------------------------------------------
            # ACTIVE SPACE
            # -----------------------------------------------------

            print()
            print("Active Space")

            active_space = formatted["active_space"]

            print(
                f"  Electrons:        "
                f"{active_space['electrons']}"
            )

            print(
                f"  Spatial Orbitals: "
                f"{active_space['spatial_orbitals']}"
            )

            print(
                f"  Selected Orbitals: {formatted['active_space']['selected_orbitals']}"
            )

            print(
                f"  Selection Method:  {formatted['active_space']['selection_method']}"
            )

            # -----------------------------------------------------
            # HAMILTONIAN
            # -----------------------------------------------------

            print()
            print("Hamiltonian")

            hamiltonian = formatted["hamiltonian"]

            print(
                f"  Qubits:      "
                f"{hamiltonian['qubits']}"
            )

            print(
                f"  Pauli Terms: "
                f"{hamiltonian['pauli_terms']}"
            )

            # -----------------------------------------------------
            # VQE DETAILS
            # -----------------------------------------------------

            print()
            print("VQE")

            print(
                f"  Optimizer:          "
                f"{formatted['optimizer']}"
            )

            print(
                f"  Maximum iterations: "
                f"{formatted['max_iterations']}"
            )

            # -----------------------------------------------------
            # ENERGY
            # -----------------------------------------------------

            print()
            print("Energy")

            print(
                f"  Ground-State Energy: "
                f"{formatted['ground_state_energy']:.6f} "
                f"{formatted['energy_unit']}"
            )

        # =========================================================
        # QAOA
        # =========================================================

        elif formatted.get("method") == "QAOA":

            print()
            print("=" * 70)
            print("                        QAOA RESULT")
            print("=" * 70)

            print()
            print(f"Method:  {formatted['method']}")
            print(f"Problem: {formatted['problem']}")

            # -----------------------------------------------------
            # PROBLEM
            # -----------------------------------------------------

            print()
            print("Problem")

            print(
                f"  Nodes: "
                f"{formatted['num_nodes']}"
            )

            # -----------------------------------------------------
            # SOLUTION
            # -----------------------------------------------------

            print()
            print("Solution")

            print(
                f"  Solution: "
                f"{formatted['solution']}"
            )

            # -----------------------------------------------------
            # PARTITIONS
            # -----------------------------------------------------

            print()
            print("Partitions")

            partitions = formatted["partitions"]

            print(
                f"  Partition 0: "
                f"{partitions['partition_0']}"
            )

            print(
                f"  Partition 1: "
                f"{partitions['partition_1']}"
            )

            # -----------------------------------------------------
            # CUT EDGES
            # -----------------------------------------------------

            print()
            print("Cut Edges")

            cut_edges = formatted["cut_edges"]

            if cut_edges:

                for edge in cut_edges:
                    print(f"  {edge}")

            else:

                print("  None")

            # -----------------------------------------------------
            # OBJECTIVE
            # -----------------------------------------------------

            print()
            print(
                f"Objective Value: "
                f"{formatted['objective_value']:.6f}"
            )

        # =========================================================
        # HAMILTONIAN SIMULATION
        # =========================================================

        elif formatted.get("method") == "Hamiltonian Simulation":

            print()
            print("=" * 70)
            print("                  HAMILTONIAN SIMULATION")
            print("=" * 70)

            print()
            print(
                f"Method:   "
                f"{formatted['method']}"
            )

            print(
                f"Molecule: "
                f"{formatted['molecule']}"
            )

            print(
                f"Basis:    "
                f"{formatted['basis']}"
            )

            # -----------------------------------------------------
            # SIMULATION
            # -----------------------------------------------------

            print()
            print("Simulation")

            print(
                f"  Qubits: "
                f"{formatted['num_qubits']}"
            )

            print(
                f"  Time:   "
                f"{formatted['time']}"
            )

            # -----------------------------------------------------
            # PROBABILITIES
            # -----------------------------------------------------

            print()
            print("State Probabilities")

            probabilities = formatted["probabilities"]

            if probabilities:

                for state, probability in probabilities.items():

                    print(
                        f"  |{state}> : "
                        f"{probability:.6f}"
                    )

            else:

                print("  No probabilities returned.")

        # =========================================================
        # UNKNOWN / OTHER RESULT
        # =========================================================

        else:

            print()
            print("=" * 70)
            print("                         RESULT")
            print("=" * 70)

            print()

            for key, value in formatted.items():

                print(
                    f"{key}: {value}"
                )

        # =========================================================
        # COMPLETE
        # =========================================================

        print()
        print("=" * 70)
        print("                    QUANTUM ANALYSIS COMPLETE")
        print("=" * 70)

    except Exception as e:

        print()
        print("=" * 70)
        print("                         ERROR")
        print("=" * 70)

        print()
        print(
            f"{type(e).__name__}: {e}"
        )

        print()
        print(
            "The Quantum Agent encountered an error "
            "while processing the request."
        )

    finally:

        try:
            await client.close()

        except Exception:
            pass


if __name__ == "__main__":
    asyncio.run(main())