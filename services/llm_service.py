import openai
from typing import List, Dict, Any, Optional
import os
from dotenv import load_dotenv
import requests
import json

# Load environment variables
load_dotenv()

class OpenRouterLLMService:
    def __init__(self):
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable is required")

        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1"
        self.default_model = "openai/gpt-3.5-turbo"  # Using a more commonly available model

    def generate_response(self,
                         context: str,
                         query: str,
                         selected_text: Optional[str] = None,
                         model: Optional[str] = None) -> str:
        """
        Generate a response based on the provided context and query
        If selected_text is provided, restrict the answer to only that text
        """
        model = model or self.default_model

        # Create the prompt based on whether we have selected text
        if selected_text:
            # Restrict to selected text only
            system_message = f"""You are a helpful assistant for the Docusaurus book. Answer questions based only on the provided selected text.
            Do not use any external knowledge or information beyond what is provided in the selected text.
            If the answer is not found in the provided text, respond with: 'This information is not available in the book.'
            Do not make up information or infer beyond what is explicitly stated in the selected text.

            Selected text: {selected_text}"""
        else:
            # Use broader context
            system_message = f"""You are a helpful assistant for the Docusaurus book. Answer questions based only on the provided book content.
            Do not use any external knowledge or information beyond what is provided in the context.
            If the answer is not found in the provided context, respond with: 'This information is not available in the book.'
            Do not make up information or infer beyond what is explicitly stated in the context.

            Context: {context}"""

        user_message = f"Question: {query}\n\nPlease provide a helpful and accurate answer based only on the information provided above. Do not include any information not explicitly mentioned in the provided text."

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            "temperature": 0.1,  # Lower temperature for more consistent, factual responses
            "max_tokens": 1000
        }

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data
            )

            response.raise_for_status()
            result = response.json()

            # Extract the content from the response
            content = result['choices'][0]['message']['content']
            return content

        except requests.exceptions.RequestException as e:
            print(f"Error calling OpenRouter API: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response content: {e.response.content}")
            raise e
        except Exception as e:
            print(f"Unexpected error in OpenRouter API call: {str(e)}")
            raise e

    def check_content_availability(self, context: str, query: str) -> bool:
        """
        Check if the context contains information relevant to the query
        This is a simple keyword-based check to determine if we should respond or say "not available"
        """
        if not context or not query:
            return False

        # Simple check: see if context contains relevant terms from query
        context_lower = context.lower()
        query_lower = query.lower()

        # Split query into words and check if some appear in context
        query_words = [word for word in query_lower.split() if len(word) > 3]  # Only consider words longer than 3 chars

        matches = 0
        for word in query_words:
            if word in context_lower:
                matches += 1

        # If at least 30% of meaningful words from query appear in context, consider it relevant
        if len(query_words) > 0:
            return (matches / len(query_words)) >= 0.3
        else:
            return True  # If no meaningful words, assume relevant

# Global instance
llm_service = OpenRouterLLMService()