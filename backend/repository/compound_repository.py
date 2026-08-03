import csv
from typing import List, Dict

class CompoundRepository:
    """
    Repository responsible for data access, specifically reading raw records from the CSV file.
    """
    def __init__(self, csv_path: str):
        self.csv_path = csv_path

    def load_raw_data(self) -> List[Dict[str, str]]:
        """
        Reads the CSV file and returns a list of raw rows as dictionaries.
        Raises FileNotFoundError if the CSV does not exist.
        """
        raw_data = []
        with open(self.csv_path, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Basic cleaning of fields
                raw_data.append({
                    "cas": row.get("cas", "").strip(),
                    "name": row.get("name", "").strip(),
                    "smiles": row.get("smiles", "").strip(),
                    "location": row.get("location", "").strip(),
                    "amount": row.get("amount", "").strip(),
                    "supplier": row.get("supplier", "").strip()
                })
        return raw_data
