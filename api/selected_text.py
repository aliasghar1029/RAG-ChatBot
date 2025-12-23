from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any
from services.llm_service import llm_service
from services.retrieval_service import retrieval_service
from services.database_service import database_service
from models.chat_models import get_db
from sqlalchemy.orm import Session
from uuid import UUID
import uuid
from utils.validation import validate_selected_text_response
from utils.logging_config import logger

router = APIRouter()

class SelectedTextRequest(BaseModel):
    selected_text: str
    question: str
    session_id: str

class SelectedTextResponse(BaseModel):
    response: str
    session_id: str

@router.post("/selected-text-question", response_model=SelectedTextResponse)
async def handle_selected_text_question(
    request: SelectedTextRequest,
    db: Session = Depends(get_db)
):
    """
    Handle questions specifically about selected text
    """
    try:
        # Validate session exists
        session_uuid = UUID(request.session_id)
        session = database_service.get_session(db, session_uuid)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Create user query record with selected text
        user_query = database_service.create_user_query(
            db,
            session.session_id,
            request.question,
            selected_text=request.selected_text
        )

        # Generate response restricted to selected text
        response_text = llm_service.generate_response(
            context="",  # We'll rely on the selected_text parameter
            query=request.question,
            selected_text=request.selected_text
        )

        # Validate that the response is based only on the selected text
        validation_result = validate_selected_text_response(
            response=response_text,
            selected_text=request.selected_text
        )

        if not validation_result["is_valid"]:
            logger.warning(f"Selected text response validation failed: {validation_result['errors']}")
            # For now, we'll still return the response but log the validation failure
            # In a production system, you might want to handle this differently
        else:
            logger.info(f"Selected text response validation passed with confidence: {validation_result.get('confidence', 0.0)}")

        # Create response record
        response_record = database_service.create_response(
            db,
            user_query.query_id,
            response_text,
            source_chunks=[],  # No chunks since we're using selected text directly
            validation_result=validation_result  # Store validation result in database
        )

        return SelectedTextResponse(
            response=response_text,
            session_id=str(session.session_id)
        )

    except Exception as e:
        print(f"Error in selected text endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing selected text question: {str(e)}")