import re
from typing import Optional, Dict, Any
from pydantic import BaseModel, validator, ValidationError
from config.app_config import app_config

class ChatRequestValidator(BaseModel):
    message: str
    session_id: Optional[str] = None
    selected_text: Optional[str] = None
    history: Optional[list] = []

    @validator('message')
    def validate_message(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Message cannot be empty')
        if len(v) > 10000:  # Limit message length
            raise ValueError('Message too long (max 10000 characters)')
        # Basic sanitization - remove potentially harmful content
        sanitized = sanitize_input(v)
        return sanitized

    @validator('session_id')
    def validate_session_id(cls, v):
        if v is not None:
            # Basic UUID format validation (not perfect, but catches obvious issues)
            if not re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', v, re.IGNORECASE):
                raise ValueError('Invalid session ID format')
        return v

    @validator('selected_text')
    def validate_selected_text(cls, v):
        if v is not None and len(v) > 50000:  # Limit selected text length
            raise ValueError('Selected text too long (max 50000 characters)')
        if v:
            sanitized = sanitize_input(v)
            return sanitized
        return v

class SearchRequestValidator(BaseModel):
    query: str
    top_k: Optional[int] = 5
    selected_text: Optional[str] = None

    @validator('query')
    def validate_query(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Query cannot be empty')
        if len(v) > 1000:  # Limit query length
            raise ValueError('Query too long (max 1000 characters)')
        sanitized = sanitize_input(v)
        return sanitized

    @validator('top_k')
    def validate_top_k(cls, v):
        if v is not None and (v < 1 or v > 20):
            raise ValueError('top_k must be between 1 and 20')
        return v

    @validator('selected_text')
    def validate_selected_text(cls, v):
        if v is not None and len(v) > 50000:  # Limit selected text length
            raise ValueError('Selected text too long (max 50000 characters)')
        if v:
            sanitized = sanitize_input(v)
            return sanitized
        return v

def sanitize_input(text: str) -> str:
    """
    Basic input sanitization to remove potentially harmful content
    """
    if not text:
        return text

    # Remove null bytes
    text = text.replace('\x00', '')

    # Remove control characters (except common whitespace)
    text = re.sub(r'[\x01-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)

    # You could add more sanitization rules here based on your specific needs
    # For example, removing script tags if accepting HTML, etc.

    return text.strip()

def validate_document_content(content: str) -> Dict[str, Any]:
    """
    Validate document content before processing
    """
    errors = []

    if not content:
        errors.append("Content cannot be empty")
    elif len(content) > 1000000:  # 1MB limit
        errors.append("Content too large (max 1MB)")

    # Check for potential encoding issues
    try:
        content.encode('utf-8')
    except UnicodeError:
        errors.append("Content contains invalid Unicode characters")

    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "sanitized_content": sanitize_input(content) if content else content
    }

def is_valid_uuid(uuid_string: str) -> bool:
    """
    Validate UUID format
    """
    import re
    uuid_regex = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
        re.IGNORECASE
    )
    return bool(uuid_regex.match(uuid_string))

def validate_api_response(response: str) -> Dict[str, Any]:
    """
    Validate API response before sending to client
    """
    errors = []

    if response is None:
        errors.append("Response cannot be None")
    elif len(response) > 100000:  # 100KB limit
        errors.append("Response too large (max 100KB)")

    # Check for potential information disclosure
    if response:
        if any(keyword in response.lower() for keyword in
               ['password', 'secret', 'api_key', 'token', 'credential']):
            errors.append("Response may contain sensitive information")

    return {
        "is_valid": len(errors) == 0,
        "errors": errors
    }


def validate_selected_text_response(response: str, selected_text: str) -> Dict[str, Any]:
    """
    Validate that the response is based only on the selected text.
    This function checks if the response content is grounded in the provided selected text.
    """
    errors = []

    if not response:
        errors.append("Response cannot be empty")
        return {
            "is_valid": False,
            "errors": errors,
            "confidence": 0.0
        }

    if not selected_text:
        errors.append("Selected text cannot be empty for validation")
        return {
            "is_valid": False,
            "errors": errors,
            "confidence": 0.0
        }

    # Convert both to lowercase for comparison
    response_lower = response.lower()
    selected_text_lower = selected_text.lower()

    # Check if response contains information not in selected text
    # This is a simple validation that looks for key phrases
    response_sentences = [s.strip() for s in re.split(r'[.!?]+', response) if s.strip()]

    invalid_sentences = []
    valid_sentences = []

    for sentence in response_sentences:
        sentence_lower = sentence.lower().strip()
        if sentence_lower:
            # Check if this sentence contains information from the selected text
            # Look for at least some overlap in meaningful words
            sentence_words = set([word for word in sentence_lower.split() if len(word) > 3])
            selected_words = set([word for word in selected_text_lower.split() if len(word) > 3])

            if sentence_words:
                # Calculate overlap
                common_words = sentence_words.intersection(selected_words)
                overlap_ratio = len(common_words) / len(sentence_words) if sentence_words else 0

                if overlap_ratio < 0.3:  # If less than 30% of meaningful words overlap
                    invalid_sentences.append(sentence)
                else:
                    valid_sentences.append(sentence)

    # If more than 50% of sentences are invalid, fail validation
    total_sentences = len(response_sentences)
    if total_sentences > 0 and len(invalid_sentences) / total_sentences > 0.5:
        errors.append(f"Response contains information not found in selected text. {len(invalid_sentences)}/{total_sentences} sentences appear to be outside the selected text context.")

    # Additional check: if the response contains phrases that clearly indicate external knowledge
    external_indicators = [
        "i don't know",
        "not in the provided text",
        "not found in the selected text",
        "not mentioned in the text",
        "not specified in the text"
    ]

    if any(indicator in response_lower for indicator in external_indicators):
        # This is actually good - it means the LLM is properly refusing to answer
        # when information isn't in the selected text
        return {
            "is_valid": True,
            "errors": [],
            "confidence": 1.0,
            "validation_note": "Response properly indicates information not available in selected text"
        }

    # Calculate confidence based on sentence overlap
    if total_sentences > 0:
        valid_ratio = len(valid_sentences) / total_sentences
        confidence = min(1.0, valid_ratio)  # Cap at 1.0
    else:
        confidence = 0.0

    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "confidence": confidence,
        "valid_sentences_count": len(valid_sentences),
        "invalid_sentences_count": len(invalid_sentences),
        "total_sentences": total_sentences
    }