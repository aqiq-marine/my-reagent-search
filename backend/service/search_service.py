from typing import List, Tuple, Dict
from rdkit import Chem
from rdkit import DataStructs
from rdkit.Chem import rdFingerprintGenerator
from rdkit.Chem.rdSubstructLibrary import SubstructLibrary

from backend.models.compound import Compound
from backend.repository.compound_repository import CompoundRepository
from backend.service.loader import Loader

class SearchService:
    """
    Service responsible for managing in-memory compounds, fingerprints,
    substructure libraries, and executing the compound searches.
    """
    def __init__(self, repository: CompoundRepository):
        self.repository = repository
        self.compounds: List[Compound] = []
        self.substruct_library: SubstructLibrary = SubstructLibrary()
        self.fingerprints = []
        self.exact_match_map: Dict[str, List[Compound]] = {}
        
        # Morgan fingerprint generator for similarity search query profiling
        self.fp_gen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)

    def load_data(self) -> None:
        """
        Loads records from CSV, constructs molecular assets and caches them in memory.
        Updates are done atomically to maintain consistency in case of parsing errors.
        """
        raw_data = self.repository.load_raw_data()
        compounds, substruct_lib = Loader.process_raw_compounds(raw_data)
        
        # Build exact match map (canonical_smiles -> list of compounds)
        exact_map: Dict[str, List[Compound]] = {}
        for compound in compounds:
            exact_map.setdefault(compound.canonical_smiles, []).append(compound)
            
        # Atomic switch of state to prevent partial/invalid states if an error occurs
        self.compounds = compounds
        self.substruct_library = substruct_lib
        self.fingerprints = [c.fingerprint for c in compounds]
        self.exact_match_map = exact_map

    def substructure_search_by_molfile(self, molfile: str) -> List[Compound]:
        """
        Performs substructure query matching using RDKit's SubstructLibrary from a Molfile.
        """
        query_mol = Chem.MolFromMolBlock(molfile)
        if query_mol is None:
            raise ValueError("Invalid Molfile provided.")
        
        matched_indices = list(self.substruct_library.GetMatches(query_mol))
        return [self.compounds[idx] for idx in matched_indices]

    def substructure_search(self, smarts: str) -> List[Compound]:
        """
        Performs substructure query matching using RDKit's SubstructLibrary.
        """
        query_mol = Chem.MolFromSmarts(smarts)
        if query_mol is None:
            raise ValueError(f"Invalid SMARTS pattern: '{smarts}'")
        
        matched_indices = list(self.substruct_library.GetMatches(query_mol))
        return [self.compounds[idx] for idx in matched_indices]

    def exact_search(self, smiles: str) -> List[Compound]:
        """
        Performs exact match searching against cached canonical SMILES using O(1) dictionary lookups.
        """
        query_mol = Chem.MolFromSmiles(smiles)
        if query_mol is None:
            raise ValueError(f"Invalid SMILES string: '{smiles}'")
        
        canonical_query = Chem.MolToSmiles(query_mol, canonical=True)
        return self.exact_match_map.get(canonical_query, [])

    def similarity_search(self, smiles: str, limit: int = 20) -> List[Tuple[Compound, float]]:
        """
        Performs Tanimoto similarity search on Morgan Fingerprints in bulk.
        """
        query_mol = Chem.MolFromSmiles(smiles)
        if query_mol is None:
            raise ValueError(f"Invalid SMILES string: '{smiles}'")
        
        query_fp = self.fp_gen.GetFingerprint(query_mol)
        if not self.fingerprints:
            return []
        
        # Perform bulk comparison
        similarities = DataStructs.BulkTanimotoSimilarity(query_fp, self.fingerprints)
        
        scored_compounds = [
            (self.compounds[idx], similarity)
            for idx, similarity in enumerate(similarities)
        ]
        
        # Sort descending by similarity score
        scored_compounds.sort(key=lambda x: x[1], reverse=True)
        
        return scored_compounds[:limit]
