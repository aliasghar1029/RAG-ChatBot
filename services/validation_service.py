from typing import List, Dict, Any, Optional
import re

class ValidationService:
    def __init__(self):
        # Phrases that indicate the response acknowledges lack of information in the book
        self.known_absence_phrases = [
            "not available in the book",
            "not found in the book",
            "not mentioned in the book",
            "no information in the book",
            "book does not contain",
            "not provided in the book",
            "not specified in the book"
        ]

    def validate_book_based_response(self, response: str, context_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate that the response is grounded in the book content
        """
        validation_result = {
            'is_valid': True,
            'issues': [],
            'confidence': 1.0
        }

        # Check if response contains known absence phrases
        response_lower = response.lower()
        has_absence_indicator = any(phrase in response_lower for phrase in self.known_absence_phrases)

        if has_absence_indicator:
            # If the response indicates info is not available, that's valid
            # as long as it's truthful to the context provided
            validation_result['confidence'] = 0.9
            return validation_result

        # Check if response is too generic or contains external knowledge indicators
        generic_indicators = [
            r"generally.*",
            r"in general.*",
            r"typically.*",
            r"usually.*",
            r"most.*",
            r"many.*",
            r"external sources.*",
            r"other sources.*",
            r"from external knowledge.*"
        ]

        for indicator in generic_indicators:
            if re.search(indicator, response_lower, re.IGNORECASE):
                validation_result['issues'].append(f"Response contains generic knowledge indicator: {indicator}")
                validation_result['is_valid'] = False
                validation_result['confidence'] = 0.3

        # Check if response references information not in context
        if context_chunks:
            # For a more thorough validation, we could check if the key facts in the response
            # are supported by the context, but for now we'll do basic validation
            context_text = " ".join([chunk['content'] for chunk in context_chunks])
            context_lower = context_text.lower()

            # If context is empty but response is detailed, that's suspicious
            if len(context_text.strip()) < 50 and len(response.strip()) > 100:
                validation_result['issues'].append("Detailed response provided with minimal context")
                validation_result['is_valid'] = False
                validation_result['confidence'] = 0.2

        return validation_result

    def validate_selected_text_response(self, response: str, selected_text: str) -> Dict[str, Any]:
        """
        Validate that the response is grounded only in the selected text
        """
        validation_result = {
            'is_valid': True,
            'issues': [],
            'confidence': 1.0
        }

        # Check if response contains known absence phrases
        response_lower = response.lower()
        has_absence_indicator = any(phrase in response_lower for phrase in self.known_absence_phrases)

        if has_absence_indicator:
            validation_result['confidence'] = 0.9
            return validation_result

        # Check if selected text is empty but response is detailed
        if not selected_text.strip() and len(response.strip()) > 50:
            validation_result['issues'].append("Response provided without selected text context")
            validation_result['is_valid'] = False
            validation_result['confidence'] = 0.1

        # For more advanced validation, we could use semantic similarity
        # to check if the response aligns with the selected text content
        if selected_text and len(response.strip()) > 20:
            # Check if response contains key terms from selected text
            selected_lower = selected_text.lower()
            response_words = set(response_lower.split())
            selected_words = set(selected_lower.split())

            # Calculate overlap
            if selected_words:
                overlap = len(response_words.intersection(selected_words))
                total_response_words = len(response_words)

                if total_response_words > 0 and (overlap / total_response_words) < 0.1:
                    # Very low overlap might indicate the response is not grounded in selected text
                    validation_result['issues'].append("Low semantic overlap between response and selected text")
                    validation_result['confidence'] = 0.5

        return validation_result

# Global instance
validation_service = ValidationService()