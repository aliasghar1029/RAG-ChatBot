from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any

router = APIRouter()

class IngestRequest(BaseModel):
    docs_dir: str = "../docs"

class IngestResponse(BaseModel):
    message: str
    chunks_processed: int

@router.post("/ingest", response_model=IngestResponse)
async def ingest_documents_endpoint(request: IngestRequest):
    """
    Endpoint to trigger document ingestion from the docs directory
    """
    # Import here to avoid circular imports
    from ingest import scan_docs_directory

    try:
        chunks = scan_docs_directory(request.docs_dir)
        return IngestResponse(
            message=f"Successfully processed {len(chunks)} document chunks",
            chunks_processed=len(chunks)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing documents: {str(e)}")