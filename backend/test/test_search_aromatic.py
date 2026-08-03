import sys
from pathlib import Path
from rdkit import Chem
from rdkit.Chem.rdSubstructLibrary import SubstructLibrary

# Create a small substructure library with benzene (loaded from SMILES)
lib = SubstructLibrary()
benzene_smiles = "C1=CC=CC=C1"
mol = Chem.MolFromSmiles(benzene_smiles)
lib.AddMol(mol)

print("Aromatic SMILES represented in Mol:")
print(Chem.MolToSmiles(mol))

# Test query 1: Aromatic SMARTS "c1ccccc1"
q1 = Chem.MolFromSmarts("c1ccccc1")
print(f"Query 1 'c1ccccc1' matches: {lib.HasMatch(q1)}")

# Test query 2: Aliphatic SMARTS with double bonds "C1=CC=CC=C1"
q2 = Chem.MolFromSmarts("C1=CC=CC=C1")
print(f"Query 2 'C1=CC=CC=C1' matches: {lib.HasMatch(q2)}")

# Test query 3: MolFromSmiles as query
q3 = Chem.MolFromSmiles("C1=CC=CC=C1")
print(f"Query 3 MolFromSmiles('C1=CC=CC=C1') matches: {lib.HasMatch(q3)}")
