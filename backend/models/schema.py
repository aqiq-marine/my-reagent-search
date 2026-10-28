from pydantic import BaseModel, Field
from typing import List, Optional

class SubstructureSearchRequest(BaseModel):
    molfile: str = Field(..., description="Molfile query for substructure matching")

class SmartsSearchRequest(BaseModel):
    smarts: str = Field(..., min_length=1, max_length=4096, description="SMARTS query string for substructure matching")

class CasSearchRequest(BaseModel):
    cas: str = Field(..., min_length=5, max_length=32, pattern=r"^\d{2,7}-\d{2}-\d$", description="CAS Registry Number")

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
