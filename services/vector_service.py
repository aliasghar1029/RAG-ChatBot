from qdrant_client import QdrantClient
from qdrant_client.http import models
from typing import List, Dict, Any, Optional
import os
from dotenv import load_dotenv
from .embedding_service import embedding_service

# Load environment variables
load_dotenv()

class QdrantVectorService:
    def __init__(self):
        url = os.getenv("QDRANT_URL")
        api_key = os.getenv("QDRANT_API_KEY")
        collection_name = os.getenv("QDRANT_COLLECTION_NAME", "book_chunks")

        if not url:
            raise ValueError("QDRANT_URL environment variable is required")
        if not api_key:
            raise ValueError("QDRANT_API_KEY environment variable is required")

        self.client = QdrantClient(
            url=url,
            api_key=api_key,
            prefer_grpc=False  # Using HTTP for compatibility
        )
        self.collection_name = collection_name
        self._ensure_collection_exists()

    def _ensure_collection_exists(self):
        """
        Ensure the collection exists with proper configuration
        """
        try:
            # Check if collection exists
            self.client.get_collection(self.collection_name)
        except:
            # Create collection if it doesn't exist
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=1024,  # Cohere's embed-multilingual-v3.0 returns 1024-dim vectors
                    distance=models.Distance.COSINE
                )
            )
            print(f"Created collection: {self.collection_name}")

    def store_chunks(self, chunks: List[Dict[str, Any]]):
        """
        Store document chunks with their embeddings in Qdrant
        Each chunk should have: chunk_id, content, document_id, title, chapter, section, source_path
        """
        points = []
        texts = []

        for chunk in chunks:
            texts.append(chunk['content'])

        # Generate embeddings for all texts at once
        embeddings = embedding_service.generate_embeddings(texts)

        for i, chunk in enumerate(chunks):
            point = models.PointStruct(
                id=chunk['chunk_id'],
                vector=embeddings[i],
                payload={
                    'content': chunk['content'],
                    'document_id': chunk.get('document_id', ''),
                    'title': chunk.get('title', ''),
                    'chapter': chunk.get('chapter', ''),
                    'section': chunk.get('section', ''),
                    'source_path': chunk.get('source_path', ''),
                    'metadata': chunk.get('metadata', {})
                }
            )
            points.append(point)

        # Upload points to Qdrant
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        print(f"Stored {len(chunks)} chunks in Qdrant collection: {self.collection_name}")

    def search_chunks(self, query: str, top_k: int = 5, selected_text: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for relevant chunks based on the query
        If selected_text is provided, search only within that text context
        """
        # Generate embedding for the query
        query_embedding = embedding_service.embed_single_text(query)

        # If selected_text is provided, we'll search with a filter for that specific content
        search_filter = None
        if selected_text:
            # In this case, we'll do a keyword search in the payload to match selected text
            # This is a simplified approach - in practice, you might want to match based on document_id
            # or other metadata that indicates the selected text context
            search_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="content",
                        match=models.MatchText(text=selected_text[:100])  # Use first 100 chars as approximation
                    )
                ]
            )

        # Perform the search
        search_results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=top_k,
            query_filter=search_filter,
            with_payload=True
        )

        # Format results
        results = []
        for result in search_results:
            results.append({
                'chunk_id': result.id,
                'content': result.payload.get('content', ''),
                'document_id': result.payload.get('document_id', ''),
                'title': result.payload.get('title', ''),
                'source_path': result.payload.get('source_path', ''),
                'chapter': result.payload.get('chapter', ''),
                'section': result.payload.get('section', ''),
                'similarity_score': result.score
            })

        return results

    def get_chunk_by_id(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific chunk by its ID
        """
        records = self.client.retrieve(
            collection_name=self.collection_name,
            ids=[chunk_id],
            with_payload=True
        )

        if records:
            record = records[0]
            payload = record.payload
            return {
                'chunk_id': record.id,
                'content': payload.get('content', ''),
                'document_id': payload.get('document_id', ''),
                'title': payload.get('title', ''),
                'source_path': payload.get('source_path', ''),
                'chapter': payload.get('chapter', ''),
                'section': payload.get('section', ''),
                'metadata': payload.get('metadata', {})
            }

        return None

# Global instance
vector_service = QdrantVectorService()