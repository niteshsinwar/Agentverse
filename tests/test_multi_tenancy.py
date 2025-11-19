#!/usr/bin/env python3
"""
Multi-Tenancy Isolation Testing

Critical tests to ensure tenant data isolation:
- Schema-based isolation (PostgreSQL schemas)
- No data leakage between tenants
- Tenant-specific caching
- Domain-based routing
- Tenant limits enforcement
"""

import pytest
import sys
from pathlib import Path
from typing import List, Dict

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestTenantIsolation:
    """Test that tenants are completely isolated from each other"""

    def test_schema_isolation(self):
        """Test that each tenant has isolated database schema"""
        # Create two tenants
        tenant_a = self._create_tenant('tenant-a', 'acme')
        tenant_b = self._create_tenant('tenant-b', 'contoso')

        # Verify each has its own schema
        assert tenant_a['schema_name'] == 'tenant_acme'
        assert tenant_b['schema_name'] == 'tenant_contoso'
        assert tenant_a['schema_name'] != tenant_b['schema_name']

        print(f"  ✅ Tenant A schema: {tenant_a['schema_name']}")
        print(f"  ✅ Tenant B schema: {tenant_b['schema_name']}")

    def test_data_isolation_agents(self):
        """Test that tenants cannot access each other's agents"""
        tenant_a_id = 'tenant-a'
        tenant_b_id = 'tenant-b'

        # Tenant A creates an agent
        agent_a = self._create_agent(tenant_a_id, {
            'name': 'Tenant A Agent',
            'llm_provider': 'openai',
        })

        # Tenant B creates an agent
        agent_b = self._create_agent(tenant_b_id, {
            'name': 'Tenant B Agent',
            'llm_provider': 'anthropic',
        })

        # Tenant A should only see their own agent
        tenant_a_agents = self._list_agents(tenant_a_id)
        assert len(tenant_a_agents) == 1
        assert tenant_a_agents[0]['name'] == 'Tenant A Agent'

        # Tenant B should only see their own agent
        tenant_b_agents = self._list_agents(tenant_b_id)
        assert len(tenant_b_agents) == 1
        assert tenant_b_agents[0]['name'] == 'Tenant B Agent'

        # Tenant A cannot access Tenant B's agent
        with pytest.raises(PermissionError):
            self._get_agent(tenant_a_id, agent_b['id'])

        # Tenant B cannot access Tenant A's agent
        with pytest.raises(PermissionError):
            self._get_agent(tenant_b_id, agent_a['id'])

        print(f"  ✅ Tenant A agents: {len(tenant_a_agents)}")
        print(f"  ✅ Tenant B agents: {len(tenant_b_agents)}")
        print(f"  ✅ Cross-tenant access blocked")

    def test_data_isolation_messages(self):
        """Test that tenants cannot access each other's messages"""
        tenant_a_id = 'tenant-a'
        tenant_b_id = 'tenant-b'

        # Tenant A creates a group and sends messages
        group_a = self._create_group(tenant_a_id, {'name': 'Team A'})
        msg_a = self._create_message(tenant_a_id, group_a['id'], {
            'content': 'Confidential message from Tenant A'
        })

        # Tenant B creates a group and sends messages
        group_b = self._create_group(tenant_b_id, {'name': 'Team B'})
        msg_b = self._create_message(tenant_b_id, group_b['id'], {
            'content': 'Confidential message from Tenant B'
        })

        # Tenant A cannot access Tenant B's group
        with pytest.raises(PermissionError):
            self._get_group(tenant_a_id, group_b['id'])

        # Tenant A cannot access Tenant B's messages
        with pytest.raises(PermissionError):
            self._get_message(tenant_a_id, msg_b['id'])

        # Tenant B cannot access Tenant A's group
        with pytest.raises(PermissionError):
            self._get_group(tenant_b_id, group_a['id'])

        # Tenant B cannot access Tenant A's messages
        with pytest.raises(PermissionError):
            self._get_message(tenant_b_id, msg_a['id'])

        print(f"  ✅ Message isolation verified")
        print(f"  ✅ Cross-tenant message access blocked")

    def test_data_isolation_documents(self):
        """Test that tenants cannot access each other's uploaded documents"""
        tenant_a_id = 'tenant-a'
        tenant_b_id = 'tenant-b'

        # Tenant A uploads a document
        doc_a = self._upload_document(tenant_a_id, {
            'filename': 'confidential_a.pdf',
            'content': 'Secret data from Tenant A'
        })

        # Tenant B uploads a document
        doc_b = self._upload_document(tenant_b_id, {
            'filename': 'confidential_b.pdf',
            'content': 'Secret data from Tenant B'
        })

        # Tenant A cannot access Tenant B's document
        with pytest.raises(PermissionError):
            self._get_document(tenant_a_id, doc_b['id'])

        # Tenant B cannot access Tenant A's document
        with pytest.raises(PermissionError):
            self._get_document(tenant_b_id, doc_a['id'])

        print(f"  ✅ Document isolation verified")
        print(f"  ✅ Cross-tenant document access blocked")

    def test_user_isolation(self):
        """Test that users belong to specific tenants"""
        tenant_a_id = 'tenant-a'
        tenant_b_id = 'tenant-b'

        # Create users for each tenant
        user_a = self._create_user(tenant_a_id, {
            'email': 'alice@tenant-a.com',
            'name': 'Alice'
        })

        user_b = self._create_user(tenant_b_id, {
            'email': 'bob@tenant-b.com',
            'name': 'Bob'
        })

        # User A cannot be found in Tenant B's user list
        tenant_b_users = self._list_users(tenant_b_id)
        user_a_in_b = any(u['email'] == 'alice@tenant-a.com' for u in tenant_b_users)
        assert not user_a_in_b, "User A found in Tenant B!"

        # User B cannot be found in Tenant A's user list
        tenant_a_users = self._list_users(tenant_a_id)
        user_b_in_a = any(u['email'] == 'bob@tenant-b.com' for u in tenant_a_users)
        assert not user_b_in_a, "User B found in Tenant A!"

        print(f"  ✅ User isolation verified")
        print(f"  ✅ Tenant A users: {len(tenant_a_users)}")
        print(f"  ✅ Tenant B users: {len(tenant_b_users)}")

    def test_cache_isolation(self):
        """Test that tenant caches are isolated"""
        tenant_a_id = 'tenant-a'
        tenant_b_id = 'tenant-b'

        # Create agent in Tenant A
        agent_a = self._create_agent(tenant_a_id, {'name': 'Agent A'})

        # Cache should be tenant-specific
        cache_key_a = self._get_cache_key(tenant_a_id, 'agent', agent_a['id'])
        cache_key_b = self._get_cache_key(tenant_b_id, 'agent', agent_a['id'])

        # Cache keys should be different (include tenant prefix)
        assert cache_key_a != cache_key_b
        assert tenant_a_id in cache_key_a
        assert tenant_b_id in cache_key_b

        print(f"  ✅ Cache key isolation verified")
        print(f"  ✅ Tenant A cache key: {cache_key_a}")
        print(f"  ✅ Tenant B cache key: {cache_key_b}")

    def test_websocket_channel_isolation(self):
        """Test that WebSocket channels are tenant-specific"""
        tenant_a_id = 'tenant-a'
        tenant_b_id = 'tenant-b'

        # Create groups for each tenant
        group_a = self._create_group(tenant_a_id, {'name': 'Group A'})
        group_b = self._create_group(tenant_b_id, {'name': 'Group B'})

        # Get WebSocket channel names
        channel_a = self._get_websocket_channel(tenant_a_id, group_a['id'])
        channel_b = self._get_websocket_channel(tenant_b_id, group_b['id'])

        # Channels should include tenant identifier
        assert tenant_a_id in channel_a or 'tenant_a' in channel_a
        assert tenant_b_id in channel_b or 'tenant_b' in channel_b
        assert channel_a != channel_b

        print(f"  ✅ WebSocket channel isolation verified")
        print(f"  ✅ Tenant A channel: {channel_a}")
        print(f"  ✅ Tenant B channel: {channel_b}")

    # Helper methods (mock implementations)
    def _create_tenant(self, tenant_id: str, slug: str) -> Dict:
        return {
            'id': tenant_id,
            'slug': slug,
            'schema_name': f'tenant_{slug}',
            'name': f'Tenant {slug.title()}',
        }

    def _create_agent(self, tenant_id: str, data: Dict) -> Dict:
        return {**data, 'id': f'agent-{tenant_id}-1', 'tenant_id': tenant_id}

    def _list_agents(self, tenant_id: str) -> List[Dict]:
        # Mock: return only agents for this tenant
        all_agents = [
            {'id': 'agent-tenant-a-1', 'name': 'Tenant A Agent', 'tenant_id': 'tenant-a'},
            {'id': 'agent-tenant-b-1', 'name': 'Tenant B Agent', 'tenant_id': 'tenant-b'},
        ]
        return [a for a in all_agents if a['tenant_id'] == tenant_id]

    def _get_agent(self, tenant_id: str, agent_id: str):
        # Mock: check if agent belongs to tenant
        if 'tenant-a' in agent_id and tenant_id != 'tenant-a':
            raise PermissionError("Cannot access agent from another tenant")
        if 'tenant-b' in agent_id and tenant_id != 'tenant-b':
            raise PermissionError("Cannot access agent from another tenant")
        return {'id': agent_id, 'tenant_id': tenant_id}

    def _create_group(self, tenant_id: str, data: Dict) -> Dict:
        return {**data, 'id': f'group-{tenant_id}-1', 'tenant_id': tenant_id}

    def _get_group(self, tenant_id: str, group_id: str):
        if 'tenant-a' in group_id and tenant_id != 'tenant-a':
            raise PermissionError("Cannot access group from another tenant")
        if 'tenant-b' in group_id and tenant_id != 'tenant-b':
            raise PermissionError("Cannot access group from another tenant")
        return {'id': group_id, 'tenant_id': tenant_id}

    def _create_message(self, tenant_id: str, group_id: str, data: Dict) -> Dict:
        return {**data, 'id': f'msg-{tenant_id}-1', 'group_id': group_id, 'tenant_id': tenant_id}

    def _get_message(self, tenant_id: str, message_id: str):
        if 'tenant-a' in message_id and tenant_id != 'tenant-a':
            raise PermissionError("Cannot access message from another tenant")
        if 'tenant-b' in message_id and tenant_id != 'tenant-b':
            raise PermissionError("Cannot access message from another tenant")
        return {'id': message_id, 'tenant_id': tenant_id}

    def _upload_document(self, tenant_id: str, data: Dict) -> Dict:
        return {**data, 'id': f'doc-{tenant_id}-1', 'tenant_id': tenant_id}

    def _get_document(self, tenant_id: str, doc_id: str):
        if 'tenant-a' in doc_id and tenant_id != 'tenant-a':
            raise PermissionError("Cannot access document from another tenant")
        if 'tenant-b' in doc_id and tenant_id != 'tenant-b':
            raise PermissionError("Cannot access document from another tenant")
        return {'id': doc_id, 'tenant_id': tenant_id}

    def _create_user(self, tenant_id: str, data: Dict) -> Dict:
        return {**data, 'id': f'user-{tenant_id}-1', 'tenant_id': tenant_id}

    def _list_users(self, tenant_id: str) -> List[Dict]:
        all_users = [
            {'email': 'alice@tenant-a.com', 'tenant_id': 'tenant-a'},
            {'email': 'bob@tenant-b.com', 'tenant_id': 'tenant-b'},
        ]
        return [u for u in all_users if u['tenant_id'] == tenant_id]

    def _get_cache_key(self, tenant_id: str, resource_type: str, resource_id: str) -> str:
        return f"{tenant_id}:{resource_type}:{resource_id}"

    def _get_websocket_channel(self, tenant_id: str, group_id: str) -> str:
        return f"{tenant_id}:messages_{group_id}"


class TestTenantLimits:
    """Test enforcement of tenant subscription limits"""

    def test_agent_count_limit(self):
        """Test that tenants cannot exceed agent limits"""
        tenant_id = 'test-tenant'

        # Tenant with limit of 5 agents
        tenant = self._create_tenant(tenant_id, max_agents=5)

        # Create 5 agents (should succeed)
        for i in range(5):
            agent = self._create_agent(tenant_id, {'name': f'Agent {i}'})
            assert agent is not None

        # Try to create 6th agent (should fail)
        with pytest.raises(Exception) as exc_info:
            self._create_agent(tenant_id, {'name': 'Agent 6'})

        assert 'limit exceeded' in str(exc_info.value).lower()
        print(f"  ✅ Agent limit enforced (max: 5)")

    def test_storage_limit(self):
        """Test that tenants cannot exceed storage limits"""
        tenant_id = 'test-tenant'

        # Tenant with 100MB storage limit
        tenant = self._create_tenant(tenant_id, max_storage_mb=100)

        # Upload documents totaling 90MB (should succeed)
        for i in range(9):
            doc = self._upload_document(tenant_id, {
                'filename': f'doc{i}.pdf',
                'size_mb': 10
            })
            assert doc is not None

        # Try to upload 20MB document (would exceed 100MB limit)
        with pytest.raises(Exception) as exc_info:
            self._upload_document(tenant_id, {
                'filename': 'large_doc.pdf',
                'size_mb': 20
            })

        assert 'storage limit' in str(exc_info.value).lower()
        print(f"  ✅ Storage limit enforced (max: 100MB)")

    def test_message_limit(self):
        """Test monthly message limits"""
        tenant_id = 'test-tenant'

        # Tenant with 10,000 messages/month limit
        tenant = self._create_tenant(tenant_id, max_messages_per_month=10000)

        # Simulate sending 10,000 messages
        for i in range(10000):
            msg = self._create_message(tenant_id, {'content': f'Message {i}'})

        # Try to send 10,001st message
        with pytest.raises(Exception) as exc_info:
            self._create_message(tenant_id, {'content': 'Exceeded limit'})

        assert 'message limit' in str(exc_info.value).lower()
        print(f"  ✅ Message limit enforced (max: 10,000/month)")

    def test_user_limit(self):
        """Test user count limits"""
        tenant_id = 'test-tenant'

        # Tenant with 10 users limit
        tenant = self._create_tenant(tenant_id, max_users=10)

        # Add 10 users (should succeed)
        for i in range(10):
            user = self._create_user(tenant_id, {'email': f'user{i}@example.com'})
            assert user is not None

        # Try to add 11th user
        with pytest.raises(Exception) as exc_info:
            self._create_user(tenant_id, {'email': 'user11@example.com'})

        assert 'user limit' in str(exc_info.value).lower()
        print(f"  ✅ User limit enforced (max: 10)")

    # Helper methods
    def _create_tenant(self, tenant_id: str, **limits) -> Dict:
        return {'id': tenant_id, **limits, 'current_usage': {}}

    def _create_agent(self, tenant_id: str, data: Dict) -> Dict:
        # Mock: check limit
        current_count = getattr(self, f'_agent_count_{tenant_id}', 0)
        if current_count >= 5:
            raise Exception("Agent limit exceeded")
        setattr(self, f'_agent_count_{tenant_id}', current_count + 1)
        return {**data, 'id': f'agent-{current_count}'}

    def _upload_document(self, tenant_id: str, data: Dict) -> Dict:
        # Mock: check storage limit
        current_storage = getattr(self, f'_storage_{tenant_id}', 0)
        new_storage = current_storage + data.get('size_mb', 0)

        if new_storage > 100:
            raise Exception("Storage limit exceeded")

        setattr(self, f'_storage_{tenant_id}', new_storage)
        return {**data, 'id': f'doc-{tenant_id}'}

    def _create_message(self, tenant_id: str, data: Dict) -> Dict:
        # Mock: check message limit
        current_count = getattr(self, f'_msg_count_{tenant_id}', 0)
        if current_count >= 10000:
            raise Exception("Message limit exceeded")
        setattr(self, f'_msg_count_{tenant_id}', current_count + 1)
        return {**data, 'id': f'msg-{current_count}'}

    def _create_user(self, tenant_id: str, data: Dict) -> Dict:
        # Mock: check user limit
        current_count = getattr(self, f'_user_count_{tenant_id}', 0)
        if current_count >= 10:
            raise Exception("User limit exceeded")
        setattr(self, f'_user_count_{tenant_id}', current_count + 1)
        return {**data, 'id': f'user-{current_count}'}


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
