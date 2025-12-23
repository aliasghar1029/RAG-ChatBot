from typing import List, Dict, Any
from services.retrieval_service import retrieval_service

def format_sources(cited_chunks: List[Dict[str, Any]]) -> str:
    """
    Format the sources for inclusion in the response
    """
    if not cited_chunks:
        return ""

    sources_text = "\n\nSources:\n"
    for i, chunk in enumerate(cited_chunks, 1):
        source_info = f"{i}. {chunk.get('title', 'Untitled')} - {chunk.get('source_path', 'Unknown path')}"
        if chunk.get('chapter'):
            source_info += f" (Chapter: {chunk.get('chapter')})"
        if chunk.get('section'):
            source_info += f" (Section: {chunk.get('section')})"
        sources_text += f"{source_info}\n"

    return sources_text

def enhance_response_with_sources(response: str, cited_chunks: List[Dict[str, Any]]) -> str:
    """
    Enhance the response by adding source citations
    """
    if not cited_chunks:
        # If no sources but response indicates info not available, don't add sources
        if "not available in the book" in response.lower():
            return response
        # Otherwise, return response as is
        return response

    # Don't add sources if the response indicates the info isn't available
    if "not available in the book" in response.lower():
        return response

    # Add source citations to the response
    sources_text = format_sources(cited_chunks)
    return response + sources_text

def validate_sources_in_response(response: str, cited_chunks: List[Dict[str, Any]]) -> bool:
    """
    Validate that the response appropriately references the cited sources
    """
    # Basic validation: if we have sources but the response says info is not available,
    # that's acceptable
    if "not available in the book" in response.lower():
        return True

    # If we have sources, the response should be substantive
    return len(response.strip()) > len("not available in the book")