from pyscf import gto, scf


# 1. Define H2 molecule
mol = gto.M(
    atom="""
    H 0 0 0
    H 0 0 0.735
    """,
    basis="sto-3g"
)

# 2. Perform Hartree-Fock calculation
mf = scf.RHF(mol)

energy = mf.kernel()

print("\n==============================")
print("      CUREGENIX QUANTUM")
print("==============================")
print("Molecule       : H2")
print("Method         : Hartree-Fock")
print("Basis Set      : STO-3G")
print(f"Energy         : {energy:.12f} Hartree")
print("==============================")