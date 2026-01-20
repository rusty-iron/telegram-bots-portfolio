"""
Нагрузочное тестирование для MeatBot
"""

import asyncio
import statistics
import time
from typing import Any, Dict, List

import aiohttp
import pytest
import structlog

logger = structlog.get_logger()


class LoadTestResults:
    """Класс для хранения результатов нагрузочного тестирования"""

    def __init__(self):
        self.response_times: List[float] = []
        self.success_count: int = 0
        self.error_count: int = 0
        self.errors: List[str] = []
        self.start_time: float = 0
        self.end_time: float = 0

    def add_response_time(self, response_time: float):
        """Добавляет время ответа"""
        self.response_times.append(response_time)

    def add_success(self):
        """Увеличивает счетчик успешных запросов"""
        self.success_count += 1

    def add_error(self, error: str):
        """Добавляет ошибку"""
        self.error_count += 1
        self.errors.append(error)

    def get_statistics(self) -> Dict[str, Any]:
        """Возвращает статистику тестирования"""
        if not self.response_times:
            return {"error": "No response times recorded"}

        total_time = self.end_time - self.start_time
        total_requests = self.success_count + self.error_count

        return {
            "total_requests": total_requests,
            "successful_requests": self.success_count,
            "failed_requests": self.error_count,
            "success_rate": (
                self.success_count /
                total_requests *
                100) if total_requests > 0 else 0,
            "total_time": total_time,
            "requests_per_second": total_requests /
            total_time if total_time > 0 else 0,
            "response_times": {
                "min": min(
                    self.response_times),
                "max": max(
                    self.response_times),
                "mean": statistics.mean(
                    self.response_times),
                "median": statistics.median(
                    self.response_times),
                "p95": self._percentile(
                    self.response_times,
                    95),
                "p99": self._percentile(
                    self.response_times,
                    99),
            },
        }

    def _percentile(self, data: List[float], percentile: int) -> float:
        """Вычисляет процентиль"""
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]


class LoadTester:
    """Класс для проведения нагрузочного тестирования"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session: aiohttp.ClientSession = None

    async def __aenter__(self):
        """Асинхронный контекстный менеджер - вход"""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Асинхронный контекстный менеджер - выход"""
        if self.session:
            await self.session.close()

    async def test_endpoint(
        self,
        endpoint: str,
        method: str = "GET",
        data: Dict[str, Any] = None,
        headers: Dict[str, str] = None,
    ) -> LoadTestResults:
        """Тестирует конкретный endpoint"""
        results = LoadTestResults()
        results.start_time = time.time()

        url = f"{self.base_url}{endpoint}"

        try:
            if method.upper() == "GET":
                async with self.session.get(url, headers=headers) as response:
                    response_time = time.time() - results.start_time
                    results.add_response_time(response_time)

                    if response.status == 200:
                        results.add_success()
                    else:
                        results.add_error(f"HTTP {response.status}")

            elif method.upper() == "POST":
                async with self.session.post(url, json=data, headers=headers) as response:
                    response_time = time.time() - results.start_time
                    results.add_response_time(response_time)

                    if response.status in [200, 201]:
                        results.add_success()
                    else:
                        results.add_error(f"HTTP {response.status}")

            else:
                results.add_error(f"Unsupported method: {method}")

        except Exception as e:
            response_time = time.time() - results.start_time
            results.add_response_time(response_time)
            results.add_error(str(e))

        results.end_time = time.time()
        return results

    async def concurrent_test(
        self,
        endpoint: str,
        concurrent_users: int,
        requests_per_user: int,
        method: str = "GET",
        data: Dict[str, Any] = None,
        headers: Dict[str, str] = None,
    ) -> LoadTestResults:
        """Проводит тестирование с заданным количеством одновременных пользователей"""
        results = LoadTestResults()
        results.start_time = time.time()

        async def user_simulation():
            """Симуляция одного пользователя"""
            user_results = LoadTestResults()

            for _ in range(requests_per_user):
                try:
                    start_time = time.time()

                    if method.upper() == "GET":
                        async with self.session.get(
                            f"{self.base_url}{endpoint}", headers=headers
                        ) as response:
                            response_time = time.time() - start_time
                            user_results.add_response_time(response_time)

                            if response.status == 200:
                                user_results.add_success()
                            else:
                                user_results.add_error(
                                    f"HTTP {response.status}")

                    elif method.upper() == "POST":
                        async with self.session.post(
                            f"{self.base_url}{endpoint}",
                            json=data,
                            headers=headers,
                        ) as response:
                            response_time = time.time() - start_time
                            user_results.add_response_time(response_time)

                            if response.status in [200, 201]:
                                user_results.add_success()
                            else:
                                user_results.add_error(
                                    f"HTTP {response.status}")

                    # Небольшая задержка между запросами
                    await asyncio.sleep(0.1)

                except Exception as e:
                    response_time = time.time() - start_time
                    user_results.add_response_time(response_time)
                    user_results.add_error(str(e))

            return user_results

        # Запускаем симуляцию пользователей
        tasks = [user_simulation() for _ in range(concurrent_users)]
        user_results_list = await asyncio.gather(*tasks)

        # Агрегируем результаты
        for user_results in user_results_list:
            results.response_times.extend(user_results.response_times)
            results.success_count += user_results.success_count
            results.error_count += user_results.error_count
            results.errors.extend(user_results.errors)

        results.end_time = time.time()
        return results


class PerformanceTestSuite:
    """Набор тестов производительности"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    async def test_health_endpoints(self):
        """Тестирует health endpoints"""
        async with LoadTester(self.base_url) as tester:
            # Тест /health/live
            results = await tester.concurrent_test(
                endpoint="/health/live",
                concurrent_users=10,
                requests_per_user=10,
            )

            stats = results.get_statistics()
            logger.info("Health live endpoint test", **stats)

            # Проверяем, что все запросы успешны
            assert (
                stats["success_rate"] == 100.0
            ), f"Health live endpoint failed: {stats['success_rate']}%"
            assert (
                stats["response_times"]["p95"] < 1.0), f"Health live endpoint too slow: {
                stats['response_times']['p95']}s"

            # Тест /health/ready
            results = await tester.concurrent_test(
                endpoint="/health/ready",
                concurrent_users=10,
                requests_per_user=10,
            )

            stats = results.get_statistics()
            logger.info("Health ready endpoint test", **stats)

            assert (
                stats["success_rate"] == 100.0
            ), f"Health ready endpoint failed: {stats['success_rate']}%"
            assert (
                stats["response_times"]["p95"] < 1.0), f"Health ready endpoint too slow: {
                stats['response_times']['p95']}s"

    async def test_metrics_endpoint(self):
        """Тестирует metrics endpoint"""
        async with LoadTester(self.base_url) as tester:
            results = await tester.concurrent_test(
                endpoint="/metrics", concurrent_users=5, requests_per_user=20
            )

            stats = results.get_statistics()
            logger.info("Metrics endpoint test", **stats)

            # Metrics endpoint может быть медленнее из-за сбора данных
            assert (
                stats["success_rate"] >= 95.0
            ), f"Metrics endpoint failed: {stats['success_rate']}%"
            assert (
                stats["response_times"]["p95"] < 2.0
            ), f"Metrics endpoint too slow: {stats['response_times']['p95']}s"

    async def test_high_load(self):
        """Тестирует высокую нагрузку"""
        async with LoadTester(self.base_url) as tester:
            results = await tester.concurrent_test(
                endpoint="/health/live",
                concurrent_users=50,
                requests_per_user=20,
            )

            stats = results.get_statistics()
            logger.info("High load test", **stats)

            # При высокой нагрузке допускаем небольшой процент ошибок
            assert stats["success_rate"] >= 90.0, f"High load test failed: {stats['success_rate']}%"
            assert (
                stats["requests_per_second"] >= 100
            ), f"Low throughput: {stats['requests_per_second']} req/s"

    async def test_sustained_load(self):
        """Тестирует длительную нагрузку"""
        async with LoadTester(self.base_url) as tester:
            results = await tester.concurrent_test(
                endpoint="/health/live",
                concurrent_users=20,
                requests_per_user=50,
            )

            stats = results.get_statistics()
            logger.info("Sustained load test", **stats)

            # При длительной нагрузке проверяем стабильность
            assert (
                stats["success_rate"] >= 95.0
            ), f"Sustained load test failed: {stats['success_rate']}%"
            assert (
                stats["response_times"]["p99"] < 5.0), f"Sustained load test too slow: {
                stats['response_times']['p99']}s"

    async def run_all_tests(self):
        """Запускает все тесты производительности"""
        logger.info("Starting performance test suite")

        try:
            await self.test_health_endpoints()
            logger.info("Health endpoints test passed")

            await self.test_metrics_endpoint()
            logger.info("Metrics endpoint test passed")

            await self.test_high_load()
            logger.info("High load test passed")

            await self.test_sustained_load()
            logger.info("Sustained load test passed")

            logger.info("All performance tests passed")

        except Exception as e:
            logger.error("Performance test failed", error=str(e))
            raise


# Pytest тесты
@pytest.mark.asyncio
async def test_health_endpoints_performance():
    """Pytest тест для health endpoints"""
    test_suite = PerformanceTestSuite()
    await test_suite.test_health_endpoints()


@pytest.mark.asyncio
async def test_metrics_endpoint_performance():
    """Pytest тест для metrics endpoint"""
    test_suite = PerformanceTestSuite()
    await test_suite.test_metrics_endpoint()


@pytest.mark.asyncio
async def test_high_load_performance():
    """Pytest тест для высокой нагрузки"""
    test_suite = PerformanceTestSuite()
    await test_suite.test_high_load()


@pytest.mark.asyncio
async def test_sustained_load_performance():
    """Pytest тест для длительной нагрузки"""
    test_suite = PerformanceTestSuite()
    await test_suite.test_sustained_load()


@pytest.mark.asyncio
async def test_full_performance_suite():
    """Pytest тест для полного набора тестов производительности"""
    test_suite = PerformanceTestSuite()
    await test_suite.run_all_tests()


# CLI интерфейс
async def main():
    """Главная функция для запуска тестов из командной строки"""
    import argparse

    parser = argparse.ArgumentParser(description="Load testing for MeatBot")
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Base URL for testing")
    parser.add_argument(
        "--test",
        choices=["health", "metrics", "high-load", "sustained", "all"],
        default="all",
        help="Test to run",
    )

    args = parser.parse_args()

    test_suite = PerformanceTestSuite(args.url)

    if args.test == "health":
        await test_suite.test_health_endpoints()
    elif args.test == "metrics":
        await test_suite.test_metrics_endpoint()
    elif args.test == "high-load":
        await test_suite.test_high_load()
    elif args.test == "sustained":
        await test_suite.test_sustained_load()
    elif args.test == "all":
        await test_suite.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
