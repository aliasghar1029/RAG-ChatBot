from typing import List, Dict, Any, Optional
from .retrieval_service import retrieval_service
from .llm_service import llm_service
from .database_service import database_service
from sqlalchemy.orm import Session

class RAGService:
    def __init__(self):
        self.retrieval_service = retrieval_service
        self.llm_service = llm_service

    def process_query(self,
                     query: str,
                     db: Session,
                     session_id: str,
                     selected_text: Optional[str] = None,
                     top_k: int = 5) -> Dict[str, Any]:
        """
        Complete RAG pipeline: Retrieve, Augment, Generate
        """
        try:
            # Step 1: Retrieve relevant chunks based on the query
            relevant_chunks = self.retrieval_service.retrieve_relevant_chunks(
                query,
                top_k=top_k,
                selected_text=selected_text
            )

            # Step 2: Prepare context from retrieved chunks
            if selected_text:
                # If selected text is provided, use only that as context
                context = selected_text
            elif relevant_chunks:
                # Otherwise use retrieved chunks as context
                context = self.retrieval_service.get_context_string(relevant_chunks)
            else:
                # If no relevant chunks found, inform the LLM
                context = ""

            # Step 3: Generate response using LLM with the context
            response = self.llm_service.generate_response(
                context=context,
                query=query,
                selected_text=selected_text
            )

            # Step 4: Store the interaction in the database
            # First, create the user query
            from uuid import UUID
            session_uuid = UUID(session_id)
            user_query = database_service.create_user_query(
                db,
                session_uuid,
                query,
                selected_text,
                context_chunks=[chunk['chunk_id'] for chunk in relevant_chunks] if relevant_chunks else []
            )

            # Then create the response
            response_record = database_service.create_response(
                db,
                user_query.query_id,
                response,
                source_chunks=[chunk['chunk_id'] for chunk in relevant_chunks] if relevant_chunks else [],
                # Calculate a basic confidence score based on similarity
                confidence_score=int(min(100, max(0, relevant_chunks[0]['similarity_score'] * 100))) if relevant_chunks else 0
            )

            # Step 5: Prepare response with sources
            sources = []
            if relevant_chunks:
                for chunk in relevant_chunks:
                    sources.append({
                        'chunk_id': chunk['chunk_id'],
                        'title': chunk['title'],
                        'source_path': chunk['source_path'],
                        'chapter': chunk['chapter'],
                        'section': chunk['section'],
                        'similarity_score': chunk['similarity_score']
                    })

            return {
                'response': response,
                'sources': sources,
                'context_chunks': relevant_chunks
            }

        except Exception as e:
            print(f"Error in RAG pipeline: {str(e)}")
            raise e

    def validate_response(self, response: str, query: str, context: str) -> bool:
        """
        Validate that the response is grounded in the provided context
        """
        # Basic validation: check if response contains phrases that indicate
        # it's acknowledging lack of information
        if "not available in the book" in response.lower():
            return True  # This is a valid response when info isn't found

        # For more advanced validation, we could check for semantic similarity
        # between the response and the context, but for now we'll return True
        return True

# Global instance
rag_service = RAGService()