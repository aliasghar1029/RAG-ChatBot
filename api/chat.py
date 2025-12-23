from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic.error_wrappers import ValidationError
from services.llm_service import llm_service
from services.retrieval_service import retrieval_service
from services.database_service import database_service
from models.chat_models import get_db
from sqlalchemy.orm import Session
from utils.validation import ChatRequestValidator, validate_api_response, validate_selected_text_response
from utils.logging_config import logger
from utils.cache import response_cache, get_cache_key
import uuid

router = APIRouter()

# Pydantic models for request/response
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    selected_text: Optional[str] = None
    history: Optional[List[Dict[str, str]]] = []

class ChatResponse(BaseModel):
    response: str
    session_id: str
    sources: List[Dict[str, str]]
    confidence: Optional[float] = None

class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5
    selected_text: Optional[str] = None

class SearchResponse(BaseModel):
    results: List[Dict[str, Any]]

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Process user query and return response based on book content
    """
    try:
        # Validate request
        validated_request = ChatRequestValidator(
            message=request.message,
            session_id=request.session_id,
            selected_text=request.selected_text,
            history=request.history
        )

        logger.info(f"Processing chat request: {validated_request.message[:50]}...")

        # Create cache key
        cache_key = get_cache_key(
            message=validated_request.message,
            selected_text=validated_request.selected_text
        )

        # Try to get response from cache
        cached_response = response_cache.get(cache_key)
        if cached_response:
            logger.info(f"Cache hit for query: {validated_request.message[:30]}...")
            return ChatResponse(**cached_response)

        # Create or retrieve session
        if validated_request.session_id:
            session_uuid = UUID(validated_request.session_id)
            session = database_service.get_session(db, session_uuid)
            if not session:
                # If session doesn't exist, create a new one
                session = database_service.create_session(db)
        else:
            session = database_service.create_session(db)

        # Create user query record
        user_query = database_service.create_user_query(
            db,
            session.session_id,
            validated_request.message,
            validated_request.selected_text
        )

        # Determine context based on whether selected text is provided
        if validated_request.selected_text:
            # Use only the selected text for context - no vector search needed
            context = f"Selected text: {validated_request.selected_text}"
            # For selected text mode, we use the selected text directly as context
            # No need to search in vector DB since we're restricting to selected text
            relevant_chunks = [{
                'chunk_id': 'selected_text',
                'title': 'Selected Text',
                'source_path': 'selected_text',
                'chapter': 'Selected',
                'section': 'Selected',
                'content': validated_request.selected_text
            }]
        else:
            # Use retrieved content from the book
            relevant_chunks = retrieval_service.retrieve_relevant_chunks(
                validated_request.message,
                top_k=5
            )

            # Build context from retrieved chunks
            if relevant_chunks:
                context = retrieval_service.get_context_string(relevant_chunks)
            else:
                context = ""

        # Generate response using LLM
        response_text = llm_service.generate_response(
            context=context,
            query=validated_request.message,
            selected_text=validated_request.selected_text
        )

        # Validate the API response
        validation_result = validate_api_response(response_text)
        if not validation_result["is_valid"]:
            logger.warning(f"Response validation failed: {validation_result['errors']}")
            response_text = "This information is not available in the book."

        # For selected text queries, perform additional validation to ensure response is based only on selected text
        final_validation_result = validation_result
        if validated_request.selected_text:
            selected_text_validation = validate_selected_text_response(
                response=response_text,
                selected_text=validated_request.selected_text
            )

            # Merge validation results
            final_validation_result = {
                "api_validation": validation_result,
                "selected_text_validation": selected_text_validation
            }

            if not selected_text_validation["is_valid"]:
                logger.warning(f"Selected text response validation failed: {selected_text_validation['errors']}")
                # For now, we'll log the issue but still return the response
                # In a production system, you might want to handle this differently
            else:
                logger.info(f"Selected text response validation passed with confidence: {selected_text_validation.get('confidence', 0.0)}")

        # Create response record
        response_record = database_service.create_response(
            db,
            user_query.query_id,
            response_text,
            source_chunks=[chunk['chunk_id'] for chunk in relevant_chunks] if relevant_chunks else [],
            validation_result=final_validation_result
        )

        # Prepare sources for response
        sources = []
        if relevant_chunks:
            for chunk in relevant_chunks:
                sources.append({
                    'chunk_id': chunk['chunk_id'],
                    'title': chunk['title'],
                    'source_path': chunk['source_path'],
                    'chapter': chunk['chapter'],
                    'section': chunk['section']
                })

        # Create response object
        response_obj = ChatResponse(
            response=response_text,
            session_id=str(session.session_id),
            sources=sources
        )

        # Cache the response
        response_cache.put(cache_key, response_obj.dict())

        logger.info(f"Chat request processed successfully: {validated_request.message[:30]}...")

        return response_obj

    except ValidationError as ve:
        logger.error(f"Validation error in chat endpoint: {ve}")
        raise HTTPException(status_code=422, detail=f"Validation error: {str(ve)}")
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing chat request: {str(e)}")

@router.post("/search", response_model=SearchResponse)
async def search_endpoint(request: SearchRequest):
    """
    Search for relevant content based on user query
    """
    try:
        # Validate request
        validated_request = SearchRequest(
            query=request.query,
            top_k=request.top_k,
            selected_text=request.selected_text
        )

        from utils.validation import SearchRequestValidator
        validated_request = SearchRequestValidator(
            query=validated_request.query,
            top_k=validated_request.top_k,
            selected_text=validated_request.selected_text
        )

        logger.info(f"Processing search request: {validated_request.query[:50]}...")

        # Create cache key
        cache_key = get_cache_key(
            query=validated_request.query,
            top_k=validated_request.top_k,
            selected_text=validated_request.selected_text
        )

        # Try to get results from cache
        cached_results = response_cache.get(f"search_{cache_key}")
        if cached_results:
            logger.info(f"Search cache hit for query: {validated_request.query[:30]}...")
            return SearchResponse(results=cached_results)

        # Perform search in vector database
        results = retrieval_service.retrieve_relevant_chunks(
            validated_request.query,
            top_k=validated_request.top_k,
            selected_text=validated_request.selected_text
        )

        # Cache the results
        response_cache.put(f"search_{cache_key}", results)

        logger.info(f"Search request processed successfully: {validated_request.query[:30]}...")

        return SearchResponse(results=results)

    except ValidationError as ve:
        logger.error(f"Validation error in search endpoint: {ve}")
        raise HTTPException(status_code=422, detail=f"Validation error: {str(ve)}")
    except Exception as e:
        logger.error(f"Error in search endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing search request: {str(e)}")