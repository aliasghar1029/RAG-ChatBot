import cohere
from typing import List, Dict, Any
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class CohereEmbeddingService:
    def __init__(self):
        api_key = os.getenv("COHERE_API_KEY")
        if not api_key:
            raise ValueError("COHERE_API_KEY environment variable is required")
        self.client = cohere.Client(api_key)
        self.model = "embed-multilingual-v3.0"  # Using the recommended model

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts using Cohere API
        """
        try:
            response = self.client.embed(
                texts=texts,
                model=self.model,
                input_type="search_document"  # Using search_document for knowledge base
            )
            return [embedding for embedding in response.embeddings]
        except Exception as e:
            print(f"Error generating embeddings: {str(e)}")
            raise e

    def embed_single_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text
        """
        embeddings = self.generate_embeddings([text])
        return embeddings[0] if embeddings else []

# Global instance
embedding_service = CohereEmbeddingService()