from rdkit import Chem
from rdkit.Chem.rdSubstructLibrary import SubstructLibrary


def main():
    aldehyde = Chem.AddHs(Chem.MolFromSmiles("CC=O"))
    ketone = Chem.AddHs(Chem.MolFromSmiles("CC(=O)C"))

    # Build a query MolBlock containing an explicit aldehyde hydrogen.
    query_source = Chem.AddHs(Chem.MolFromSmiles("CC=O"))
    query = Chem.MolFromMolBlock(
        Chem.MolToMolBlock(query_source), removeHs=False
    )

    assert query.GetNumAtoms() > 2
    assert aldehyde.HasSubstructMatch(query)
    assert not ketone.HasSubstructMatch(query)

    library = SubstructLibrary()
    library.AddMol(aldehyde)
    library.AddMol(ketone)
    assert list(library.GetMatches(query)) == [0]
    print("Explicit hydrogen substructure matching: passed")


if __name__ == "__main__":
    main()
