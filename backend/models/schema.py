from pydantic import BaseModel, Field
from typing import List, Optional

class SubstructureSearchRequest(BaseModel):
    molfile: str = Field(..., description="Molfile query for substructure matching")

class ExactSearchRequest(BaseModel):
    smiles: str = Field(..., description="SMILES query string for exact matching")

class SimilaritySearchRequest(BaseModel):
    smiles: str = Field(..., description="SMILES query string for similarity matching")
    limit: int = Field(default=20, ge=1, description="Maximum number of results to return")

class SearchResultItem(BaseModel):
    cas: str
    name: str
    location: str
    supplier: str
    svg: str
    similarity: Optional[float] = None

class SearchResponse(BaseModel):
    count: int
    items: List[SearchResultItem]
