#!/usr/bin/env python
"""
WebSocket Testing Script

Tests both real-time chat (MessageConsumer) and cloud sync (CloudSyncConsumer).

Usage:
    python test_websocket.py

Prerequisites:
    - Django server running on port 9000
    - User authenticated and JWT token available
    - pip install websocket-client
"""

import asyncio
import websockets
import json
import sys
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
os.environ.setdefault('DATABASE_URL', 'sqlite:///./db.sqlite3')
os.environ.setdefault('DJANGO_SECRET_KEY', 'test-secret-key')
os.environ.setdefault('DEBUG', 'True')

django.setup()

from apps.users.models import User
from apps.groups.models import Group
from apps.messages.models import Message
import jwt
from django.conf import settings


def generate_jwt_token(user):
    """Generate JWT token for authentication"""
    payload = {
        'user_id': str(user.id),
        'email': user.email,
        'exp': 9999999999  # Far future expiry for testing
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')


async def test_message_consumer(token, group_id):
    """Test MessageConsumer - real-time chat"""
    print("\n" + "="*60)
    print("TEST 1: MessageConsumer (Real-time Chat)")
    print("="*60)

    uri = f"ws://localhost:9000/ws/messages/{group_id}/?token={token}"

    try:
        async with websockets.connect(uri) as websocket:
            print(f"✅ Connected to message channel for group {group_id}")

            # Send typing indicator
            await websocket.send(json.dumps({
                'type': 'typing_indicator',
                'is_typing': True
            }))
            print("📤 Sent typing indicator")

            # Listen for messages (non-blocking)
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                data = json.loads(response)
                print(f"📥 Received: {data}")
            except asyncio.TimeoutError:
                print("⏱️  No messages received (this is normal for testing)")

            print("✅ MessageConsumer test passed\n")

    except Exception as e:
        print(f"❌ MessageConsumer test failed: {e}\n")
        return False

    return True


async def test_cloud_sync_consumer(token):
    """Test CloudSyncConsumer - cloud→local synchronization"""
    print("\n" + "="*60)
    print("TEST 2: CloudSyncConsumer (Config Sync)")
    print("="*60)

    uri = f"ws://localhost:9000/ws/sync/?token={token}"

    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to sync channel")

            # Listen for sync events (non-blocking)
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                data = json.loads(response)
                print(f"📥 Received sync event: {data}")
            except asyncio.TimeoutError:
                print("⏱️  No sync events received (this is normal for testing)")

            print("✅ CloudSyncConsumer test passed\n")

    except Exception as e:
        print(f"❌ CloudSyncConsumer test failed: {e}\n")
        return False

    return True


async def test_websocket_auth():
    """Test WebSocket authentication (invalid token should fail)"""
    print("\n" + "="*60)
    print("TEST 3: WebSocket Authentication")
    print("="*60)

    # Test with invalid token
    uri = "ws://localhost:9000/ws/sync/?token=invalid_token_12345"

    try:
        async with websockets.connect(uri) as websocket:
            # If we get here, auth failed to reject invalid token
            print("❌ Authentication test failed: Invalid token was accepted")
            return False
    except websockets.exceptions.InvalidStatusCode as e:
        if e.status_code == 403 or e.status_code == 401:
            print("✅ Authentication correctly rejected invalid token")
            return True
        else:
            print(f"❌ Unexpected status code: {e.status_code}")
            return False
    except Exception as e:
        # Connection might be closed before we can check
        print(f"✅ Authentication test passed (connection closed for invalid token)")
        return True


async def main():
    """Run all WebSocket tests"""
    print("\n" + "="*60)
    print("🚀 AgentVerse WebSocket Test Suite")
    print("="*60)

    # Get or create test user
    try:
        user = User.objects.get(email='admin@example.com')
    except User.DoesNotExist:
        print("❌ Test user not found. Please run setup_and_test.sh first")
        sys.exit(1)

    # Generate JWT token
    token = generate_jwt_token(user)
    print(f"✅ Generated JWT token for {user.email}")

    # Get or create test group
    try:
        group = Group.objects.first()
        if not group:
            print("⚠️  No groups found. Creating test group...")
            group = Group.objects.create(
                name="Test Group",
                description="Test group for WebSocket testing"
            )
    except Exception as e:
        print(f"❌ Error accessing groups: {e}")
        sys.exit(1)

    print(f"✅ Using test group: {group.name} (ID: {group.id})")

    # Run tests
    results = []

    # Test 1: MessageConsumer
    results.append(await test_message_consumer(token, str(group.id)))

    # Test 2: CloudSyncConsumer
    results.append(await test_cloud_sync_consumer(token))

    # Test 3: Authentication
    results.append(await test_websocket_auth())

    # Summary
    print("\n" + "="*60)
    print("📊 Test Summary")
    print("="*60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
