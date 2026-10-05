MOLECULES = {
    "LiH": {
        "atom": "Li 0 0 0; H 0 0 1.6",
        "default_basis": "sto3g",
    },
    "H2": {
        "atom": "H 0 0 0; H 0 0 0.735",
        "default_basis": "sto3g",
    },
}


def get_molecule(name: str):
    for molecule_name, data in MOLECULES.items():
        if molecule_name.lower() == name.lower():
            return {
                "name": molecule_name,
                **data,
            }

    return None