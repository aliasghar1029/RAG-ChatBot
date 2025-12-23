from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from services.retrieval_service import retrieval_service

router = APIRouter()

class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5
    selected_text: Optional[str] = None

class SearchResponse(BaseModel):
    results: List[Dict[str, Any]]

@router.post("/search", response_model=SearchResponse)
async def search_endpoint(request: SearchRequest):
    """
    Search for relevant content based on user query
    """
    try:
        # Perform search in vector database
        results = retrieval_service.retrieve_relevant_chunks(
            request.query,
            top_k=request.top_k,
            selected_text=request.selected_text
        )

        return SearchResponse(results=results)

    except Exception as e:
        print(f"Error in search endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing search request: {str(e)}")