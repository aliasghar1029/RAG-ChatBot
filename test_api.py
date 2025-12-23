import asyncio
import aiohttp
import time
from typing import Dict, Any, List
import json

class ChatbotAPITester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def test_health_endpoint(self) -> Dict[str, Any]:
        """Test the health endpoint"""
        try:
            async with self.session.get(f"{self.base_url}/api/health") as response:
                return {
                    "status": response.status,
                    "body": await response.json(),
                    "success": response.status == 200
                }
        except Exception as e:
            return {
                "status": 0,
                "error": str(e),
                "success": False
            }

    async def test_chat_endpoint(self, message: str, selected_text: str = None) -> Dict[str, Any]:
        """Test the chat endpoint"""
        try:
            payload = {
                "message": message,
                "selected_text": selected_text
            }

            start_time = time.time()
            async with self.session.post(f"{self.base_url}/api/chat", json=payload) as response:
                response_time = time.time() - start_time
                return {
                    "status": response.status,
                    "body": await response.json(),
                    "response_time": response_time,
                    "success": response.status == 200
                }
        except Exception as e:
            return {
                "status": 0,
                "error": str(e),
                "success": False
            }

    async def test_search_endpoint(self, query: str) -> Dict[str, Any]:
        """Test the search endpoint"""
        try:
            payload = {"query": query}
            async with self.session.post(f"{self.base_url}/api/search", json=payload) as response:
                return {
                    "status": response.status,
                    "body": await response.json(),
                    "success": response.status == 200
                }
        except Exception as e:
            return {
                "status": 0,
                "error": str(e),
                "success": False
            }

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all validation tests"""
        results = {
            "health_check": await self.test_health_endpoint(),
            "chat_test": await self.test_chat_endpoint("What is this book about?"),
            "search_test": await self.test_search_endpoint("book content"),
            "selected_text_test": await self.test_chat_endpoint(
                "Explain this selection",
                "This is a sample text selection for testing."
            )
        }

        # Performance test
        performance_results = await self.test_performance()
        results["performance"] = performance_results

        # Summary
        all_success = all(test["success"] for test in results.values() if isinstance(test, dict) and "success" in test)

        results["summary"] = {
            "all_tests_passed": all_success,
            "total_tests": len([k for k in results.keys() if k != "summary"]),
            "passed_tests": len([k for k, v in results.items() if k != "summary" and isinstance(v, dict) and v.get("success", False)])
        }

        return results

    async def test_performance(self) -> Dict[str, Any]:
        """Test performance metrics"""
        try:
            # Test response time for multiple requests
            response_times = []
            for i in range(3):
                start_time = time.time()
                await self.test_chat_endpoint(f"Test message {i}")
                response_time = time.time() - start_time
                response_times.append(response_time)

            avg_response_time = sum(response_times) / len(response_times) if response_times else 0

            return {
                "avg_response_time": avg_response_time,
                "max_response_time": max(response_times) if response_times else 0,
                "min_response_time": min(response_times) if response_times else 0,
                "target_response_time": 5.0,  # 5 seconds target
                "meets_performance": avg_response_time <= 5.0
            }
        except Exception as e:
            return {
                "error": str(e),
                "meets_performance": False
            }

async def main():
    async with ChatbotAPITester() as tester:
        print("Running validation tests...")
        results = await tester.run_all_tests()

        print("\n=== TEST RESULTS ===")
        for test_name, result in results.items():
            if test_name == "summary":
                continue
            status = "✅ PASS" if result.get("success", False) else "❌ FAIL"
            print(f"{test_name}: {status}")
            if "response_time" in result:
                print(f"  Response time: {result['response_time']:.2f}s")

        print(f"\n=== SUMMARY ===")
        summary = results["summary"]
        print(f"Tests passed: {summary['passed_tests']}/{summary['total_tests']}")
        print(f"All tests passed: {'✅ YES' if summary['all_tests_passed'] else '❌ NO'}")

        if "performance" in results:
            perf = results["performance"]
            if "meets_performance" in perf:
                perf_status = "✅ PASS" if perf["meets_performance"] else "❌ FAIL"
                print(f"Performance (avg response time {perf['avg_response_time']:.2f}s): {perf_status}")

if __name__ == "__main__":
    asyncio.run(main())