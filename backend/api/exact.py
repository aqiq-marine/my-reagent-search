from fastapi import APIRouter, Depends, HTTPException, Request
from backend.models.schema import ExactSearchRequest, SearchResponse, SearchResultItem
from backend.service.search_service import SearchService

router = APIRouter()

def get_search_service(request: Request) -> SearchService:
    return request.app.state.search_service

@router.post("/exact", response_model=SearchResponse)
def search_exact(
    request_data: ExactSearchRequest,
    search_service: SearchService = Depends(get_search_service)
):
    try:
        results = search_service.exact_search(request_data.smiles)
        items = [
            SearchResultItem(
                cas=c.cas,
                name=c.name,
                location=c.location,
                supplier=c.supplier,
                svg=c.svg,
                similarity=None
            )
            for c in results
        ]
        return SearchResponse(count=len(items), items=items)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal exact search error: {str(e)}")
