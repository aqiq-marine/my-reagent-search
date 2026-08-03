import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from backend.repository.compound_repository import CompoundRepository
from backend.service.search_service import SearchService

CSV_PATH = Path("backend/data/reagent.csv")
repository = CompoundRepository(str(CSV_PATH))
search_service = SearchService(repository)
search_service.load_data()

print(f"Loaded {len(search_service.compounds)} compounds.")

# Test 1: Substructure search for Iodine
# SMILES CI has I. Let's search with SMARTS "[#53]" (Iodine)
print("\n--- Test 1: Iodine [I] ---")
results = search_service.substructure_search("[#53]")
print(f"Found {len(results)} matches for '[#53]'.")
for r in results[:5]:
    print(f"  CAS: {r.cas}, SMILES: {r.connectivity_smiles}, Name: {r.name}")

# Test 2: Substructure search for Benzene ring
print("\n--- Test 2: Benzene c1ccccc1 ---")
results = search_service.substructure_search("c1ccccc1")
print(f"Found {len(results)} matches for 'c1ccccc1'.")
for r in results[:5]:
    print(f"  CAS: {r.cas}, SMILES: {r.connectivity_smiles}, Name: {r.name}")

# Test 3: Substructure search for Carbonyl C=O
print("\n--- Test 3: Carbonyl C=O ---")
results = search_service.substructure_search("C=O")
print(f"Found {len(results)} matches for 'C=O'.")
for r in results[:5]:
    print(f"  CAS: {r.cas}, SMILES: {r.connectivity_smiles}, Name: {r.name}")
