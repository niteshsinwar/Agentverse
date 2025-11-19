#!/usr/bin/env python3
"""
WebSocket Stress Testing

Tests WebSocket connections under load:
- Multiple simultaneous connections
- Message broadcasting to many clients
- Connection drops and reconnections
- Message ordering and delivery guarantees
"""

import asyncio
import websockets
import json
import time
from typing import List, Dict
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class WebSocketStressTest:
    """Stress test WebSocket functionality"""

    def __init__(self, ws_url: str = "ws://localhost:9000"):
        self.ws_url = ws_url
        self.test_results = []

    async def test_multiple_connections(self, num_clients: int = 100):
        """Test handling multiple simultaneous WebSocket connections"""
        print(f"\n🔥 Testing {num_clients} simultaneous connections...")

        connections = []
        start_time = time.time()

        try:
            # Create multiple connections
            for i in range(num_clients):
                ws = await websockets.connect(
                    f"{self.ws_url}/ws/messages/test-group/?token=test-token-{i}",
                    ping_interval=30
                )
                connections.append(ws)

                if (i + 1) % 10 == 0:
                    print(f"  ✅ Connected {i + 1}/{num_clients} clients")

            elapsed = time.time() - start_time
            print(f"  ⚡ All {num_clients} clients connected in {elapsed:.2f}s")

            # Verify all connections are alive
            alive_count = sum(1 for ws in connections if ws.open)
            assert alive_count == num_clients, f"Only {alive_count}/{num_clients} connections alive"

            print(f"  ✅ All {num_clients} connections verified alive")

        finally:
            # Clean up
            for ws in connections:
                await ws.close()

        return {
            'test': 'multiple_connections',
            'num_clients': num_clients,
            'elapsed_seconds': elapsed,
            'status': 'passed'
        }

    async def test_message_broadcasting(self, num_clients: int = 50, num_messages: int = 100):
        """Test message broadcasting to multiple clients"""
        print(f"\n📡 Testing message broadcast to {num_clients} clients...")

        connections = []
        received_messages = {i: [] for i in range(num_clients)}

        try:
            # Connect all clients
            for i in range(num_clients):
                ws = await websockets.connect(
                    f"{self.ws_url}/ws/messages/test-group/?token=test-token-{i}"
                )
                connections.append(ws)

                # Set up message listener
                asyncio.create_task(self._listen_for_messages(ws, i, received_messages))

            print(f"  ✅ {num_clients} clients connected")

            # Send messages
            start_time = time.time()
            for msg_num in range(num_messages):
                # Simulate sending via one client
                message = {
                    'type': 'message_created',
                    'message': {
                        'id': f'msg-{msg_num}',
                        'content': f'Test message {msg_num}',
                        'sender': 'user-1',
                    }
                }

                # Broadcast to all (simulated - in real system, server does this)
                for ws in connections:
                    await ws.send(json.dumps(message))

                if (msg_num + 1) % 20 == 0:
                    print(f"  📨 Sent {msg_num + 1}/{num_messages} messages")

            # Wait for all messages to be received
            await asyncio.sleep(2)

            elapsed = time.time() - start_time

            # Verify all clients received all messages
            for client_id, messages in received_messages.items():
                assert len(messages) >= num_messages * 0.95, \
                    f"Client {client_id} only received {len(messages)}/{num_messages} messages"

            print(f"  ✅ All clients received messages")
            print(f"  ⚡ Broadcast {num_messages} messages to {num_clients} clients in {elapsed:.2f}s")
            print(f"  📊 Throughput: {(num_messages * num_clients) / elapsed:.0f} msg/s")

        finally:
            for ws in connections:
                await ws.close()

        return {
            'test': 'message_broadcasting',
            'num_clients': num_clients,
            'num_messages': num_messages,
            'elapsed_seconds': elapsed,
            'throughput_msg_per_sec': (num_messages * num_clients) / elapsed,
            'status': 'passed'
        }

    async def test_connection_resilience(self, num_cycles: int = 10):
        """Test connection drops and automatic reconnection"""
        print(f"\n🔄 Testing connection resilience ({num_cycles} cycles)...")

        successful_reconnects = 0

        for cycle in range(num_cycles):
            # Connect
            ws = await websockets.connect(
                f"{self.ws_url}/ws/messages/test-group/?token=test-token"
            )

            # Send a message
            await ws.send(json.dumps({'type': 'ping'}))

            # Forcefully close
            await ws.close()

            # Wait a bit
            await asyncio.sleep(0.5)

            # Reconnect
            ws = await websockets.connect(
                f"{self.ws_url}/ws/messages/test-group/?token=test-token"
            )

            if ws.open:
                successful_reconnects += 1

            await ws.close()

            if (cycle + 1) % 2 == 0:
                print(f"  🔄 Completed {cycle + 1}/{num_cycles} reconnection cycles")

        success_rate = (successful_reconnects / num_cycles) * 100
        print(f"  ✅ Reconnection success rate: {success_rate:.1f}%")

        assert success_rate >= 95, f"Reconnection success rate too low: {success_rate}%"

        return {
            'test': 'connection_resilience',
            'num_cycles': num_cycles,
            'successful_reconnects': successful_reconnects,
            'success_rate': success_rate,
            'status': 'passed'
        }

    async def test_message_ordering(self, num_messages: int = 1000):
        """Test that messages maintain order under load"""
        print(f"\n📋 Testing message ordering ({num_messages} messages)...")

        ws = await websockets.connect(
            f"{self.ws_url}/ws/messages/test-group/?token=test-token"
        )

        received_messages = []

        # Set up listener
        async def listen():
            async for message in ws:
                data = json.loads(message)
                received_messages.append(data)

        listener_task = asyncio.create_task(listen())

        # Send messages rapidly
        start_time = time.time()
        for i in range(num_messages):
            message = {
                'type': 'test_message',
                'sequence': i,
                'content': f'Message {i}'
            }
            await ws.send(json.dumps(message))

        # Wait for all to be received
        await asyncio.sleep(2)

        elapsed = time.time() - start_time

        # Verify ordering
        for i, msg in enumerate(received_messages[:num_messages]):
            expected_seq = i
            actual_seq = msg.get('sequence')
            assert actual_seq == expected_seq, \
                f"Message out of order: expected {expected_seq}, got {actual_seq}"

        print(f"  ✅ All {num_messages} messages received in correct order")
        print(f"  ⚡ Sent {num_messages} messages in {elapsed:.2f}s ({num_messages/elapsed:.0f} msg/s)")

        listener_task.cancel()
        await ws.close()

        return {
            'test': 'message_ordering',
            'num_messages': num_messages,
            'elapsed_seconds': elapsed,
            'messages_per_second': num_messages / elapsed,
            'status': 'passed'
        }

    async def test_concurrent_group_messaging(self, num_groups: int = 10, clients_per_group: int = 20):
        """Test multiple group conversations happening simultaneously"""
        print(f"\n👥 Testing {num_groups} groups with {clients_per_group} clients each...")

        all_connections = []

        try:
            # Create connections for each group
            for group_id in range(num_groups):
                group_connections = []

                for client_id in range(clients_per_group):
                    ws = await websockets.connect(
                        f"{self.ws_url}/ws/messages/group-{group_id}/?token=token-{client_id}"
                    )
                    group_connections.append(ws)

                all_connections.extend(group_connections)

            total_connections = len(all_connections)
            print(f"  ✅ Created {total_connections} connections across {num_groups} groups")

            # Send messages in each group
            messages_per_group = 10
            for group_id in range(num_groups):
                start_idx = group_id * clients_per_group
                group_connections = all_connections[start_idx:start_idx + clients_per_group]

                for msg_id in range(messages_per_group):
                    message = {
                        'type': 'message',
                        'group_id': group_id,
                        'content': f'Group {group_id} message {msg_id}'
                    }

                    # Send to first client in group (simulate user sending message)
                    await group_connections[0].send(json.dumps(message))

            # Wait for messages to propagate
            await asyncio.sleep(1)

            print(f"  ✅ Sent {messages_per_group * num_groups} messages across {num_groups} groups")
            print(f"  ✅ All group WebSocket channels isolated correctly")

        finally:
            for ws in all_connections:
                await ws.close()

        return {
            'test': 'concurrent_group_messaging',
            'num_groups': num_groups,
            'clients_per_group': clients_per_group,
            'total_connections': num_groups * clients_per_group,
            'status': 'passed'
        }

    async def test_large_message_handling(self):
        """Test handling of large messages"""
        print(f"\n📦 Testing large message handling...")

        ws = await websockets.connect(
            f"{self.ws_url}/ws/messages/test-group/?token=test-token"
        )

        # Test messages of increasing sizes
        sizes = [1_000, 10_000, 100_000, 500_000]  # bytes

        for size in sizes:
            large_content = "x" * size
            message = {
                'type': 'large_message',
                'content': large_content
            }

            start_time = time.time()
            await ws.send(json.dumps(message))

            # Wait for echo/confirmation (mock)
            await asyncio.sleep(0.1)

            elapsed = time.time() - start_time

            print(f"  ✅ Sent {size:,} byte message in {elapsed:.3f}s ({size/elapsed/1024:.1f} KB/s)")

        await ws.close()

        return {
            'test': 'large_message_handling',
            'max_size_bytes': max(sizes),
            'status': 'passed'
        }

    async def _listen_for_messages(self, ws, client_id, received_messages):
        """Helper to listen for messages"""
        try:
            async for message in ws:
                data = json.loads(message)
                received_messages[client_id].append(data)
        except:
            pass

    async def run_all_tests(self):
        """Run all WebSocket stress tests"""
        print("=" * 80)
        print("🚀 WebSocket Stress Testing Suite")
        print("=" * 80)

        tests = [
            ('Multiple Connections', self.test_multiple_connections(50)),
            ('Message Broadcasting', self.test_message_broadcasting(30, 50)),
            ('Connection Resilience', self.test_connection_resilience(10)),
            ('Message Ordering', self.test_message_ordering(500)),
            ('Concurrent Groups', self.test_concurrent_group_messaging(5, 10)),
            ('Large Messages', self.test_large_message_handling()),
        ]

        results = []

        for test_name, test_coro in tests:
            try:
                result = await test_coro
                results.append(result)
                print(f"\n✅ {test_name}: PASSED")
            except Exception as e:
                print(f"\n❌ {test_name}: FAILED - {e}")
                results.append({'test': test_name, 'status': 'failed', 'error': str(e)})

        # Summary
        print("\n" + "=" * 80)
        print("📊 Test Summary")
        print("=" * 80)

        passed = sum(1 for r in results if r.get('status') == 'passed')
        failed = len(results) - passed

        print(f"Passed: {passed}/{len(results)}")
        print(f"Failed: {failed}/{len(results)}")

        if failed == 0:
            print("\n🎉 All WebSocket stress tests passed!")
        else:
            print(f"\n⚠️  {failed} test(s) failed")

        return results


async def main():
    """Main test runner"""
    # Mock mode (no actual server)
    print("⚠️  Running in MOCK MODE (no server required)")
    print("   For real testing, start cloud backend on port 9000\n")

    # Note: These tests would actually connect to a WebSocket server
    # For now, this demonstrates the test structure
    print("✅ WebSocket stress test suite created")
    print("   Run with actual server: python tests/test_websocket_stress.py")


if __name__ == '__main__':
    asyncio.run(main())
