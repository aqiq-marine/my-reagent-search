from fastapi import APIRouter, HTTPException, Request

from backend.models.schema import CasSearchRequest, SearchResponse, SearchResultItem
from backend.service.search_service import SearchService

router = APIRouter()

def get_search_service(request: Request) -> SearchService:
    return request.app.state.search_service

@router.post("/cas", response_model=SearchResponse)
def search_cas(request_data: CasSearchRequest, request: Request):
    try:
        service = get_search_service(request)
        results = service.cas_search(request_data.cas)
        return SearchResponse(count=len(results), items=[
            SearchResultItem(cas=c.cas, name=c.name, location=c.location, supplier=c.supplier, svg=c.svg)
            for c in results
        ])
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Internal CAS search error: {exc}")
