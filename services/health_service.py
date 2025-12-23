from typing import Dict, Any
from services.embedding_service import embedding_service
from services.vector_service import vector_service
from services.llm_service import llm_service

class HealthService:
    @staticmethod
    def check_all_services() -> Dict[str, Any]:
        """
        Check the health status of all external services
        """
        services_status = {
            "cohere": "disconnected",
            "qdrant": "disconnected",
            "openrouter": "disconnected",
            "database": "not_implemented"  # Database health check not implemented yet
        }

        # Check Cohere API
        try:
            # Test with a simple embedding to verify API key works
            test_embedding = embedding_service.embed_single_text("health check")
            if test_embedding and len(test_embedding) > 0:
                services_status["cohere"] = "connected"
        except Exception:
            services_status["cohere"] = "disconnected"

        # Check Qdrant connection
        try:
            # Try to get collection info to verify connection
            collection_info = vector_service.client.get_collection(vector_service.collection_name)
            if collection_info:
                services_status["qdrant"] = "connected"
        except Exception:
            services_status["qdrant"] = "disconnected"

        # Check OpenRouter API
        try:
            # Test with a simple request to verify API key works
            test_response = llm_service.generate_response(
                context="This is a health check.",
                query="Is the service working?"
                # Using default model from llm_service
            )
            if test_response:
                services_status["openrouter"] = "connected"
        except Exception:
            services_status["openrouter"] = "disconnected"

        # Overall status
        connected_count = sum(1 for status in services_status.values() if status == "connected")
        total_count = len(services_status)

        overall_status = "healthy" if connected_count == total_count else "degraded" if connected_count > 0 else "unhealthy"

        return {
            "status": overall_status,
            "timestamp": __import__('datetime').datetime.now().isoformat(),
            "services": services_status,
            "connected_services": connected_count,
            "total_services": total_count
        }

# Global instance
health_service = HealthService()