import sys
import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure the parent directory is in sys.path to enable imports of the "backend" package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.repository.compound_repository import CompoundRepository
from backend.service.search_service import SearchService
from backend.api import substructure, exact, similarity, reload

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = Path(os.environ["REAGENT_DB"]) if os.environ.get("REAGENT_DB") else BASE_DIR / "data" / "reagent.csv"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize repository and search service on startup
    repository = CompoundRepository(str(CSV_PATH))
    search_service = SearchService(repository)
    
    # Load and build data structures
    search_service.load_data()
    
    # Set to app state
    app.state.search_service = search_service
    
    yield
    # Cleanup if needed (none required for in-memory lists)

app = FastAPI(
    title="Reagent Search API",
    description="RDKit-powered chemical structure and property search service",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS for integration with the Vite + React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register endpoints from routers
app.include_router(substructure.router, prefix="/search", tags=["Search"])
app.include_router(exact.router, prefix="/search", tags=["Search"])
app.include_router(similarity.router, prefix="/search", tags=["Search"])
app.include_router(reload.router, tags=["Management"])

if __name__ == "__main__":
    import uvicorn
    # Start the server on port 8000
    host = "127.0.0.1"

    hot_reload = os.environ.get("RELEASE", "").lower() != "true"
    uvicorn.run("backend.main:app", host=host, port=8000, reload=hot_reload)
