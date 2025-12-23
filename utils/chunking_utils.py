import tiktoken
import re
from typing import List, Dict, Any
from uuid import uuid5, NAMESPACE_URL

# Initialize tokenizer for chunking
tokenizer = tiktoken.get_encoding("cl100k_base")

def clean_text(text: str) -> str:
    """
    Clean text by removing extra whitespace and normalizing
    """
    # Remove extra whitespace and newlines
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def chunk_text_by_tokens(text: str, max_tokens: int = 500, overlap_tokens: int = 50) -> List[str]:
    """
    Split text into chunks of approximately max_tokens with overlap
    """
    if not text.strip():
        return []

    # Tokenize the text
    tokens = tokenizer.encode(text)

    chunks = []
    start_idx = 0

    while start_idx < len(tokens):
        # Determine the end index for this chunk
        end_idx = start_idx + max_tokens

        # If this is not the last chunk, add overlap
        if end_idx < len(tokens):
            end_idx += overlap_tokens

        # Extract the token chunk
        token_chunk = tokens[start_idx:end_idx]

        # Decode back to text
        chunk_text = tokenizer.decode(token_chunk)
        chunk_text = clean_text(chunk_text)

        if chunk_text:  # Only add non-empty chunks
            chunks.append(chunk_text)

        # Move start index forward by max_tokens (not including overlap for next iteration)
        start_idx += max_tokens

    return chunks

def chunk_text_by_sentences(text: str, max_tokens: int = 500) -> List[str]:
    """
    Split text into chunks by sentences, respecting token limits
    """
    if not text.strip():
        return []

    # Split by sentences
    sentences = re.split(r'[.!?]+\s+', text)
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        # Check if adding this sentence would exceed the token limit
        test_chunk = current_chunk + " " + sentence if current_chunk else sentence
        token_count = len(tokenizer.encode(test_chunk))

        if token_count <= max_tokens:
            current_chunk = test_chunk
        else:
            # If current chunk is not empty, save it and start a new one
            if current_chunk.strip():
                chunks.append(clean_text(current_chunk))
            # If the sentence itself is too long, chunk it by tokens
            if len(tokenizer.encode(sentence)) > max_tokens:
                sub_chunks = chunk_text_by_tokens(sentence, max_tokens, 0)
                chunks.extend(sub_chunks)
            else:
                current_chunk = sentence

    # Add the last chunk if it exists
    if current_chunk.strip():
        chunks.append(clean_text(current_chunk))

    return chunks

def create_chunk_dict(content: str, source_path: str, document_id: str,
                     title: str = "", chapter: str = "", section: str = "",
                     metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Create a properly formatted chunk dictionary with all required fields
    """
    if metadata is None:
        metadata = {}

    chunk_id = str(uuid5(NAMESPACE_URL, f"{source_path}_{len(content)}_{hash(content)}"))

    return {
        'chunk_id': chunk_id,
        'content': content,
        'document_id': document_id,
        'title': title,
        'chapter': chapter,
        'section': section,
        'source_path': source_path,
        'metadata': metadata
    }

def chunk_document(content: str, source_path: str, document_id: str,
                  title: str = "", chapter: str = "", section: str = "",
                  chunk_method: str = "tokens", max_tokens: int = 500,
                  overlap_tokens: int = 50) -> List[Dict[str, Any]]:
    """
    Chunk a document using the specified method
    """
    if chunk_method == "sentences":
        chunks = chunk_text_by_sentences(content, max_tokens)
    else:  # default to tokens
        chunks = chunk_text_by_tokens(content, max_tokens, overlap_tokens)

    # Convert each chunk string to a proper chunk dictionary
    chunk_dicts = []
    for i, chunk_content in enumerate(chunks):
        chunk_dict = create_chunk_dict(
            content=chunk_content,
            source_path=source_path,
            document_id=document_id,
            title=title,
            chapter=chapter,
            section=section,
            metadata={
                'chunk_index': i,
                'total_chunks': len(chunks),
                'method': chunk_method
            }
        )
        chunk_dicts.append(chunk_dict)

    return chunk_dicts