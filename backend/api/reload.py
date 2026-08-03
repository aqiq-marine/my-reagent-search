from fastapi import APIRouter, Depends, HTTPException, Request
from backend.service.search_service import SearchService

router = APIRouter()

def get_search_service(request: Request) -> SearchService:
    return request.app.state.search_service

@router.post("/reload")
def reload_library(
    search_service: SearchService = Depends(get_search_service)
):
    try:
        search_service.load_data()
        return {
            "status": "success",
            "message": f"Library reloaded successfully. Loaded {len(search_service.compounds)} compounds."
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"CSV processing error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reload library: {str(e)}")
