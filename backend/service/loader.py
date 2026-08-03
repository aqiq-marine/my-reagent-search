from typing import List, Tuple, Dict
from rdkit import Chem
from rdkit.Chem.Draw import rdMolDraw2D
from rdkit.Chem import rdFingerprintGenerator
from rdkit.Chem.rdSubstructLibrary import SubstructLibrary
from backend.models.compound import Compound

import logging

logger = logging.getLogger(__name__)

class Loader:
    """
    Service responsible for converting raw chemical data into RDKit-enriched Compound objects
    and building the SubstructLibrary.
    """
    @staticmethod
    def process_raw_compounds(raw_data: List[Dict[str, str]]) -> Tuple[List[Compound], SubstructLibrary]:
        compounds = []
        substruct_library = SubstructLibrary()
        
        # Initialize Morgan Fingerprint Generator (radius 2, 2048 bits)
        fp_gen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
        
        for idx, row in enumerate(raw_data):
            smiles = row.get("smiles", "")
            cas = row.get("cas", "")
            name = row.get("name", "")
            location = row.get("location", "")
            amount = row.get("amount", "")
            supplier = row.get("supplier", "")
            
            if not smiles:
                logger.warning(f"Missing SMILES for compound '{name}' (CAS: {cas}) at row {idx+1}. Skipping.")
                continue
            
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                logger.warning(f"Invalid SMILES '{smiles}' for compound '{name}' (CAS: {cas}) at row {idx+1}. Skipping.")
                continue
            
            # Canonical SMILES
            canonical_smiles = Chem.MolToSmiles(mol, canonical=True)
            
            # Morgan Fingerprint
            fp = fp_gen.GetFingerprint(mol)
            
            # SVG Generation
            # 250px width and 200px height is a good size for cards
            drawer = rdMolDraw2D.MolDraw2DSVG(250, 200)
            
            # Draw options: set transparent background if possible
            drawer.drawOptions().clearBackground = True
            
            rdMolDraw2D.PrepareAndDrawMolecule(drawer, mol)
            drawer.FinishDrawing()
            svg_text = drawer.GetDrawingText()
            
            # Extract raw <svg> tag content (stripping XML declaration if present)
            if "<?xml" in svg_text:
                svg_start = svg_text.find("<svg")
                if svg_start != -1:
                    svg_text = svg_text[svg_start:]
            
            compound = Compound(
                cas=cas,
                name=name,
                connectivity_smiles=smiles,
                canonical_smiles=canonical_smiles,
                location=location,
                amount=amount,
                supplier=supplier,
                mol=mol,
                fingerprint=fp,
                svg=svg_text
            )
            
            compounds.append(compound)
            # Add to SubstructLibrary
            substruct_library.AddMol(mol)
            
        return compounds, substruct_library
