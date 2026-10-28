from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

from fastapi import APIRouter, HTTPException, Request

from backend.models.schema import SmartsSearchRequest, SearchResponse, SearchResultItem

router = APIRouter()
SMARTS_TIMEOUT_SECONDS = 5
_smarts_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="smarts-search")

@router.post("/smarts", response_model=SearchResponse)
def search_smarts(request_data: SmartsSearchRequest, request: Request):
    try:
        future = _smarts_executor.submit(
            request.app.state.search_service.substructure_search_by_smarts,
            request_data.smarts,
        )
        try:
            results = future.result(timeout=SMARTS_TIMEOUT_SECONDS)
        except FuturesTimeoutError:
            future.cancel()
            raise HTTPException(status_code=408, detail="SMARTS search timed out")
        return SearchResponse(count=len(results), items=[
            SearchResultItem(cas=c.cas, name=c.name, location=c.location, supplier=c.supplier, svg=c.svg)
            for c in results
        ])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Internal SMARTS search error: {exc}")
