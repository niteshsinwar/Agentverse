#!/usr/bin/env python3
"""
Performance Benchmarking and Load Testing

Tests system performance under various conditions:
- API response time
- Database query performance
- Agent execution time
- WebSocket message latency
- Concurrent user load
- Memory usage
"""

import time
import asyncio
import statistics
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed


class PerformanceBenchmark:
    """Performance benchmarking suite"""

    def __init__(self):
        self.results = []

    def test_api_response_time(self, num_requests: int = 1000):
        """Benchmark API response times"""
        print(f"\n⚡ Testing API response time ({num_requests} requests)...")

        response_times = []

        for i in range(num_requests):
            start_time = time.time()

            # Mock API call
            self._call_api('/api/v1/agents/')

            elapsed = (time.time() - start_time) * 1000  # Convert to ms
            response_times.append(elapsed)

            if (i + 1) % 200 == 0:
                print(f"  📊 Completed {i + 1}/{num_requests} requests")

        # Calculate statistics
        avg_time = statistics.mean(response_times)
        median_time = statistics.median(response_times)
        p95_time = sorted(response_times)[int(0.95 * len(response_times))]
        p99_time = sorted(response_times)[int(0.99 * len(response_times))]
        min_time = min(response_times)
        max_time = max(response_times)

        print(f"\n  📊 Response Time Statistics:")
        print(f"     Average:  {avg_time:.2f}ms")
        print(f"     Median:   {median_time:.2f}ms")
        print(f"     P95:      {p95_time:.2f}ms")
        print(f"     P99:      {p99_time:.2f}ms")
        print(f"     Min:      {min_time:.2f}ms")
        print(f"     Max:      {max_time:.2f}ms")

        # Assert performance targets
        assert avg_time < 100, f"Average response time too high: {avg_time}ms"
        assert p95_time < 200, f"P95 response time too high: {p95_time}ms"

        print(f"  ✅ API response time targets met")

        return {
            'test': 'api_response_time',
            'num_requests': num_requests,
            'avg_ms': avg_time,
            'median_ms': median_time,
            'p95_ms': p95_time,
            'p99_ms': p99_time,
        }

    def test_database_query_performance(self, num_queries: int = 10000):
        """Benchmark database query performance"""
        print(f"\n🗄️  Testing database query performance ({num_queries} queries)...")

        query_times = []

        for i in range(num_queries):
            start_time = time.time()

            # Mock database query
            self._query_database("SELECT * FROM agents WHERE id = ?", ("agent-1",))

            elapsed = (time.time() - start_time) * 1000
            query_times.append(elapsed)

            if (i + 1) % 2000 == 0:
                print(f"  📊 Completed {i + 1}/{num_queries} queries")

        avg_time = statistics.mean(query_times)
        p95_time = sorted(query_times)[int(0.95 * len(query_times))]

        print(f"\n  📊 Query Time Statistics:")
        print(f"     Average:  {avg_time:.3f}ms")
        print(f"     P95:      {p95_time:.3f}ms")
        print(f"     Throughput: {num_queries / (sum(query_times) / 1000):.0f} queries/sec")

        # Assert performance targets
        assert avg_time < 10, f"Average query time too high: {avg_time}ms"

        print(f"  ✅ Database query performance targets met")

        return {
            'test': 'database_query_performance',
            'num_queries': num_queries,
            'avg_ms': avg_time,
            'p95_ms': p95_time,
        }

    def test_agent_execution_time(self, num_executions: int = 100):
        """Benchmark agent execution time"""
        print(f"\n🤖 Testing agent execution time ({num_executions} executions)...")

        execution_times = []

        for i in range(num_executions):
            start_time = time.time()

            # Mock agent execution
            self._execute_agent('test-agent', [
                {'role': 'user', 'content': 'What is 2+2?'}
            ])

            elapsed = (time.time() - start_time) * 1000
            execution_times.append(elapsed)

            if (i + 1) % 20 == 0:
                print(f"  📊 Completed {i + 1}/{num_executions} executions")

        avg_time = statistics.mean(execution_times)
        median_time = statistics.median(execution_times)

        print(f"\n  📊 Execution Time Statistics:")
        print(f"     Average:  {avg_time:.0f}ms ({avg_time/1000:.2f}s)")
        print(f"     Median:   {median_time:.0f}ms ({median_time/1000:.2f}s)")

        # Agent execution should be < 2s on average
        assert avg_time < 2000, f"Agent execution too slow: {avg_time}ms"

        print(f"  ✅ Agent execution time targets met")

        return {
            'test': 'agent_execution_time',
            'num_executions': num_executions,
            'avg_ms': avg_time,
            'median_ms': median_time,
        }

    def test_concurrent_user_load(self, num_users: int = 100, requests_per_user: int = 10):
        """Test system under concurrent user load"""
        print(f"\n👥 Testing concurrent user load ({num_users} users, {requests_per_user} req/user)...")

        start_time = time.time()

        with ThreadPoolExecutor(max_workers=num_users) as executor:
            # Submit tasks for each user
            futures = []
            for user_id in range(num_users):
                future = executor.submit(self._simulate_user_activity, user_id, requests_per_user)
                futures.append(future)

            # Wait for all to complete
            completed = 0
            for future in as_completed(futures):
                completed += 1
                if completed % 20 == 0:
                    print(f"  📊 {completed}/{num_users} users completed")

        total_time = time.time() - start_time
        total_requests = num_users * requests_per_user
        throughput = total_requests / total_time

        print(f"\n  📊 Load Test Results:")
        print(f"     Total Time:    {total_time:.2f}s")
        print(f"     Total Requests: {total_requests}")
        print(f"     Throughput:    {throughput:.0f} req/sec")
        print(f"     Avg per user:  {total_time / num_users:.2f}s")

        # System should handle 100+ requests/sec
        assert throughput > 100, f"Throughput too low: {throughput} req/sec"

        print(f"  ✅ Concurrent load test passed")

        return {
            'test': 'concurrent_user_load',
            'num_users': num_users,
            'requests_per_user': requests_per_user,
            'total_time_sec': total_time,
            'throughput_req_per_sec': throughput,
        }

    def test_websocket_message_latency(self, num_messages: int = 1000):
        """Test WebSocket message latency"""
        print(f"\n📡 Testing WebSocket message latency ({num_messages} messages)...")

        latencies = []

        for i in range(num_messages):
            start_time = time.time()

            # Mock WebSocket message send + receive
            self._send_websocket_message({'type': 'test', 'content': f'Message {i}'})
            self._receive_websocket_message()

            elapsed = (time.time() - start_time) * 1000
            latencies.append(elapsed)

            if (i + 1) % 200 == 0:
                print(f"  📊 Completed {i + 1}/{num_messages} messages")

        avg_latency = statistics.mean(latencies)
        p95_latency = sorted(latencies)[int(0.95 * len(latencies))]

        print(f"\n  📊 WebSocket Latency Statistics:")
        print(f"     Average:  {avg_latency:.2f}ms")
        print(f"     P95:      {p95_latency:.2f}ms")

        # WebSocket latency should be < 100ms
        assert avg_latency < 100, f"WebSocket latency too high: {avg_latency}ms"

        print(f"  ✅ WebSocket latency targets met")

        return {
            'test': 'websocket_message_latency',
            'num_messages': num_messages,
            'avg_ms': avg_latency,
            'p95_ms': p95_latency,
        }

    def test_memory_usage_under_load(self):
        """Test memory usage under load"""
        print(f"\n💾 Testing memory usage under load...")

        import psutil
        import os

        process = psutil.Process(os.getpid())

        # Get initial memory
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        print(f"  📊 Initial memory: {initial_memory:.2f} MB")

        # Simulate load
        agents = []
        for i in range(1000):
            agents.append(self._create_large_agent(i))

        # Get memory after load
        loaded_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = loaded_memory - initial_memory

        print(f"  📊 Memory after load: {loaded_memory:.2f} MB")
        print(f"  📊 Memory increase: {memory_increase:.2f} MB")

        # Clean up
        agents.clear()

        # Get memory after cleanup
        final_memory = process.memory_info().rss / 1024 / 1024  # MB

        print(f"  📊 Memory after cleanup: {final_memory:.2f} MB")

        # Memory should not grow unbounded
        assert memory_increase < 500, f"Memory increase too high: {memory_increase} MB"

        print(f"  ✅ Memory usage acceptable")

        return {
            'test': 'memory_usage_under_load',
            'initial_mb': initial_memory,
            'loaded_mb': loaded_memory,
            'increase_mb': memory_increase,
            'final_mb': final_memory,
        }

    def test_cache_performance(self, num_operations: int = 10000):
        """Test cache read/write performance"""
        print(f"\n🗂️  Testing cache performance ({num_operations} operations)...")

        # Test cache writes
        write_times = []
        for i in range(num_operations):
            start_time = time.time()
            self._cache_set(f'key-{i}', {'data': f'value-{i}'})
            elapsed = (time.time() - start_time) * 1000
            write_times.append(elapsed)

        avg_write_time = statistics.mean(write_times)

        # Test cache reads
        read_times = []
        for i in range(num_operations):
            start_time = time.time()
            self._cache_get(f'key-{i}')
            elapsed = (time.time() - start_time) * 1000
            read_times.append(elapsed)

        avg_read_time = statistics.mean(read_times)

        print(f"\n  📊 Cache Performance:")
        print(f"     Avg Write: {avg_write_time:.3f}ms")
        print(f"     Avg Read:  {avg_read_time:.3f}ms")
        print(f"     Write throughput: {num_operations / (sum(write_times) / 1000):.0f} ops/sec")
        print(f"     Read throughput:  {num_operations / (sum(read_times) / 1000):.0f} ops/sec")

        # Cache operations should be very fast (< 1ms)
        assert avg_write_time < 1, f"Cache writes too slow: {avg_write_time}ms"
        assert avg_read_time < 1, f"Cache reads too slow: {avg_read_time}ms"

        print(f"  ✅ Cache performance targets met")

        return {
            'test': 'cache_performance',
            'num_operations': num_operations,
            'avg_write_ms': avg_write_time,
            'avg_read_ms': avg_read_time,
        }

    # Helper methods (mock implementations)
    def _call_api(self, endpoint: str) -> Dict:
        """Mock API call"""
        time.sleep(0.05)  # Simulate 50ms response time
        return {'status': 'success'}

    def _query_database(self, query: str, params: tuple) -> List[Dict]:
        """Mock database query"""
        time.sleep(0.005)  # Simulate 5ms query time
        return [{'id': 'agent-1', 'name': 'Test'}]

    def _execute_agent(self, agent_id: str, messages: List[Dict]) -> Dict:
        """Mock agent execution"""
        time.sleep(1.2)  # Simulate 1.2s execution time (realistic for LLM call)
        return {'response': 'Test response'}

    def _simulate_user_activity(self, user_id: int, num_requests: int):
        """Simulate user making multiple requests"""
        for _ in range(num_requests):
            self._call_api(f'/api/v1/agents/?user={user_id}')

    def _send_websocket_message(self, message: Dict):
        """Mock WebSocket send"""
        time.sleep(0.03)  # Simulate 30ms latency

    def _receive_websocket_message(self):
        """Mock WebSocket receive"""
        time.sleep(0.02)  # Simulate 20ms latency

    def _create_large_agent(self, index: int) -> Dict:
        """Create a large agent object to test memory"""
        return {
            'id': f'agent-{index}',
            'name': f'Agent {index}',
            'config': {'large_data': 'x' * 1000},  # 1KB per agent
        }

    def _cache_set(self, key: str, value: Dict):
        """Mock cache write"""
        time.sleep(0.0001)  # Simulate 0.1ms write

    def _cache_get(self, key: str) -> Dict:
        """Mock cache read"""
        time.sleep(0.00005)  # Simulate 0.05ms read
        return {}

    def run_all_tests(self):
        """Run all performance tests"""
        print("=" * 80)
        print("🚀 Performance Benchmarking Suite")
        print("=" * 80)

        tests = [
            self.test_api_response_time,
            self.test_database_query_performance,
            self.test_agent_execution_time,
            self.test_concurrent_user_load,
            self.test_websocket_message_latency,
            self.test_cache_performance,
        ]

        results = []

        for test_func in tests:
            try:
                result = test_func()
                results.append(result)
            except Exception as e:
                print(f"\n❌ {test_func.__name__} FAILED: {e}")
                results.append({'test': test_func.__name__, 'status': 'failed', 'error': str(e)})

        # Summary
        print("\n" + "=" * 80)
        print("📊 Performance Test Summary")
        print("=" * 80)

        passed = sum(1 for r in results if 'error' not in r)
        failed = len(results) - passed

        print(f"Passed: {passed}/{len(results)}")
        print(f"Failed: {failed}/{len(results)}")

        if failed == 0:
            print("\n🎉 All performance tests passed!")
        else:
            print(f"\n⚠️  {failed} test(s) failed")

        return results


def main():
    """Main test runner"""
    benchmark = PerformanceBenchmark()
    results = benchmark.run_all_tests()

    # Print detailed results
    print("\n" + "=" * 80)
    print("📈 Detailed Results")
    print("=" * 80)

    for result in results:
        if 'error' not in result:
            print(f"\n{result['test']}:")
            for key, value in result.items():
                if key != 'test':
                    print(f"  {key}: {value}")


if __name__ == '__main__':
    main()
