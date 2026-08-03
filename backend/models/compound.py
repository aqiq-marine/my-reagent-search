from dataclasses import dataclass
from rdkit.Chem import Mol
from rdkit.DataStructs import ExplicitBitVect

@dataclass
class Compound:
    cas: str
    name: str
    connectivity_smiles: str
    canonical_smiles: str
    location: str
    amount: str
    supplier: str
    mol: Mol
    fingerprint: ExplicitBitVect
    svg: str
