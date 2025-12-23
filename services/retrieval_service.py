from typing import List, Dict, Any, Optional
from .vector_service import vector_service
from .embedding_service import embedding_service

class RetrievalService:
    def __init__(self):
        self.vector_service = vector_service

    def retrieve_relevant_chunks(self, query: str, top_k: int = 5, selected_text: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve the most relevant chunks for a given query
        """
        return self.vector_service.search_chunks(query, top_k, selected_text)

    def retrieve_with_context(self, query: str, top_k: int = 5, context_window: int = 2) -> List[Dict[str, Any]]:
        """
        Retrieve chunks with additional context from surrounding chunks
        """
        # First, get the most relevant chunks
        relevant_chunks = self.vector_service.search_chunks(query, top_k)

        # For each relevant chunk, we might want to get additional context
        # This would require storing chunk order information during ingestion
        # For now, we'll return the relevant chunks with their similarity scores
        return relevant_chunks

    def retrieve_and_rank(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve chunks and potentially re-rank them based on additional criteria
        """
        chunks = self.retrieve_relevant_chunks(query, top_k)

        # Simple re-ranking based on similarity score and content relevance
        # In a more advanced implementation, we could use cross-encoder re-ranking
        for chunk in chunks:
            # Add a composite score that considers both similarity and other factors
            chunk['composite_score'] = chunk['similarity_score']

        # Sort by composite score
        chunks.sort(key=lambda x: x['composite_score'], reverse=True)
        return chunks

    def get_context_string(self, chunks: List[Dict[str, Any]]) -> str:
        """
        Convert a list of chunks to a single context string for LLM
        """
        context_parts = []
        for chunk in chunks:
            context_part = f"Source: {chunk['source_path']} | Chapter: {chunk['chapter']} | Section: {chunk['section']}\n"
            context_part += f"Content: {chunk['content']}\n"
            context_parts.append(context_part)

        return "\n---\n".join(context_parts)

# Global instance
retrieval_service = RetrievalService()