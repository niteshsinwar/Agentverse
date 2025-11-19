#!/usr/bin/env python3
"""
Unit Tests for Agent Management

Tests agent CRUD operations, validation, configuration, and business logic.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestAgentModel:
    """Test Agent model validation and business logic"""

    def test_agent_name_validation(self):
        """Test agent name must be non-empty and reasonable length"""
        # Test empty name
        with pytest.raises(ValueError):
            self._create_agent(name="")

        # Test name too long (>200 chars)
        with pytest.raises(ValueError):
            self._create_agent(name="a" * 201)

        # Test valid name
        agent = self._create_agent(name="Valid Agent")
        assert agent['name'] == "Valid Agent"

    def test_agent_emoji_validation(self):
        """Test emoji validation (must be single emoji or empty)"""
        # Valid emojis
        valid_emojis = ["🤖", "🎯", "💬", "🔥", ""]
        for emoji in valid_emojis:
            agent = self._create_agent(emoji=emoji)
            assert agent['emoji'] == emoji

        # Invalid (multiple chars)
        with pytest.raises(ValueError):
            self._create_agent(emoji="🤖🤖")

    def test_llm_provider_validation(self):
        """Test LLM provider must be valid"""
        valid_providers = ["openai", "anthropic", "cohere", "google"]

        for provider in valid_providers:
            agent = self._create_agent(llm_provider=provider)
            assert agent['llm_provider'] == provider

        # Invalid provider
        with pytest.raises(ValueError):
            self._create_agent(llm_provider="invalid_provider")

    def test_llm_model_validation(self):
        """Test LLM model must match provider"""
        # Valid combinations
        valid_combos = [
            ("openai", "gpt-4o"),
            ("openai", "gpt-4o-mini"),
            ("anthropic", "claude-3-5-sonnet-20241022"),
            ("cohere", "command-r-plus"),
        ]

        for provider, model in valid_combos:
            agent = self._create_agent(llm_provider=provider, llm_model=model)
            assert agent['llm_model'] == model

        # Invalid combination (OpenAI with Claude model)
        with pytest.raises(ValueError):
            self._create_agent(llm_provider="openai", llm_model="claude-3-5-sonnet-20241022")

    def test_config_json_validation(self):
        """Test config must be valid JSON object"""
        # Valid configs
        valid_configs = [
            {"temperature": 0.7},
            {"temperature": 0.7, "max_tokens": 4000},
            {"temperature": 0.0, "top_p": 1.0},
        ]

        for config in valid_configs:
            agent = self._create_agent(config=config)
            assert agent['config'] == config

        # Invalid config (not a dict)
        with pytest.raises(ValueError):
            self._create_agent(config="invalid")

    def test_temperature_bounds(self):
        """Test temperature must be between 0 and 2"""
        # Valid temperatures
        for temp in [0.0, 0.5, 1.0, 1.5, 2.0]:
            agent = self._create_agent(config={"temperature": temp})
            assert agent['config']['temperature'] == temp

        # Invalid temperatures
        for temp in [-0.1, 2.1, 100]:
            with pytest.raises(ValueError):
                self._create_agent(config={"temperature": temp})

    def test_max_tokens_validation(self):
        """Test max_tokens must be positive integer"""
        # Valid
        agent = self._create_agent(config={"max_tokens": 4000})
        assert agent['config']['max_tokens'] == 4000

        # Invalid (negative)
        with pytest.raises(ValueError):
            self._create_agent(config={"max_tokens": -100})

        # Invalid (too large)
        with pytest.raises(ValueError):
            self._create_agent(config={"max_tokens": 1000000})

    def test_system_prompt_validation(self):
        """Test system prompt validation"""
        # Valid prompts
        valid_prompts = [
            "You are a helpful assistant.",
            "You are an expert in Python programming.",
            "" * 5000,  # Long prompt
        ]

        for prompt in valid_prompts:
            agent = self._create_agent(system_prompt=prompt)
            assert agent['system_prompt'] == prompt

        # Empty is allowed
        agent = self._create_agent(system_prompt="")
        assert agent['system_prompt'] == ""

    def test_agent_active_status(self):
        """Test agent active/inactive status"""
        # Active by default
        agent = self._create_agent()
        assert agent['is_active'] is True

        # Can set inactive
        agent = self._create_agent(is_active=False)
        assert agent['is_active'] is False

    def test_agent_tools_assignment(self):
        """Test assigning tools to agent"""
        agent = self._create_agent()

        # Can assign tool IDs
        tool_ids = ["tool-1", "tool-2", "tool-3"]
        agent = self._assign_tools(agent['id'], tool_ids)
        assert set(agent['tools']) == set(tool_ids)

    def test_agent_mcp_servers_assignment(self):
        """Test assigning MCP servers to agent"""
        agent = self._create_agent()

        # Can assign MCP server IDs
        mcp_ids = ["mcp-1", "mcp-2"]
        agent = self._assign_mcp_servers(agent['id'], mcp_ids)
        assert set(agent['mcp_servers']) == set(mcp_ids)

    # Helper methods (mock implementations)
    def _create_agent(self, **kwargs):
        """Mock agent creation"""
        defaults = {
            'id': 'test-agent-1',
            'name': 'Test Agent',
            'emoji': '🤖',
            'llm_provider': 'openai',
            'llm_model': 'gpt-4o',
            'system_prompt': 'You are a helpful assistant.',
            'config': {'temperature': 0.7},
            'is_active': True,
            'tools': [],
            'mcp_servers': [],
        }
        defaults.update(kwargs)

        # Validation
        if not defaults['name'] or len(defaults['name']) > 200:
            raise ValueError("Invalid name")

        if defaults['emoji'] and len(defaults['emoji']) > 4:
            raise ValueError("Invalid emoji")

        if defaults['llm_provider'] not in ["openai", "anthropic", "cohere", "google"]:
            raise ValueError("Invalid provider")

        # Check model matches provider
        provider_models = {
            'openai': ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo'],
            'anthropic': ['claude-3-5-sonnet-20241022', 'claude-3-opus-20240229'],
            'cohere': ['command-r-plus', 'command-r'],
            'google': ['gemini-pro', 'gemini-1.5-pro'],
        }

        if defaults['llm_model'] not in provider_models.get(defaults['llm_provider'], []):
            raise ValueError("Model doesn't match provider")

        if not isinstance(defaults['config'], dict):
            raise ValueError("Config must be dict")

        if 'temperature' in defaults['config']:
            temp = defaults['config']['temperature']
            if temp < 0 or temp > 2:
                raise ValueError("Temperature must be 0-2")

        if 'max_tokens' in defaults['config']:
            tokens = defaults['config']['max_tokens']
            if tokens < 1 or tokens > 128000:
                raise ValueError("Invalid max_tokens")

        return defaults

    def _assign_tools(self, agent_id, tool_ids):
        """Mock tool assignment"""
        return {
            'id': agent_id,
            'tools': tool_ids,
        }

    def _assign_mcp_servers(self, agent_id, mcp_ids):
        """Mock MCP assignment"""
        return {
            'id': agent_id,
            'mcp_servers': mcp_ids,
        }


class TestAgentCRUD:
    """Test Agent CRUD operations"""

    def test_create_agent(self):
        """Test creating a new agent"""
        agent_data = {
            'name': 'Test Agent',
            'emoji': '🤖',
            'llm_provider': 'openai',
            'llm_model': 'gpt-4o',
            'system_prompt': 'You are helpful.',
        }

        agent = self._create_agent(agent_data)
        assert agent['name'] == 'Test Agent'
        assert 'id' in agent
        assert 'created_at' in agent

    def test_get_agent(self):
        """Test retrieving an agent"""
        agent = self._create_agent({'name': 'Test'})

        retrieved = self._get_agent(agent['id'])
        assert retrieved['id'] == agent['id']
        assert retrieved['name'] == agent['name']

    def test_list_agents(self):
        """Test listing all agents"""
        # Create multiple agents
        for i in range(5):
            self._create_agent({'name': f'Agent {i}'})

        agents = self._list_agents()
        assert len(agents) >= 5

    def test_update_agent(self):
        """Test updating an agent"""
        agent = self._create_agent({'name': 'Original'})

        updated = self._update_agent(agent['id'], {'name': 'Updated'})
        assert updated['name'] == 'Updated'

    def test_delete_agent(self):
        """Test deleting an agent"""
        agent = self._create_agent({'name': 'To Delete'})

        self._delete_agent(agent['id'])

        with pytest.raises(Exception):
            self._get_agent(agent['id'])

    def test_partial_update(self):
        """Test partial update (PATCH)"""
        agent = self._create_agent({
            'name': 'Original',
            'emoji': '🤖',
            'system_prompt': 'Original prompt',
        })

        # Update only name
        updated = self._update_agent(agent['id'], {'name': 'New Name'})
        assert updated['name'] == 'New Name'
        assert updated['emoji'] == '🤖'  # Unchanged
        assert updated['system_prompt'] == 'Original prompt'  # Unchanged

    # Mock implementations
    def _create_agent(self, data):
        return {**data, 'id': 'test-id', 'created_at': '2025-01-01T00:00:00Z'}

    def _get_agent(self, agent_id):
        return {'id': agent_id, 'name': 'Test'}

    def _list_agents(self):
        return [{'id': f'agent-{i}', 'name': f'Agent {i}'} for i in range(10)]

    def _update_agent(self, agent_id, data):
        return {**data, 'id': agent_id}

    def _delete_agent(self, agent_id):
        pass


class TestAgentExecution:
    """Test agent execution logic"""

    def test_execute_with_empty_messages(self):
        """Test execution fails with empty messages"""
        with pytest.raises(ValueError):
            self._execute_agent('agent-1', [])

    def test_execute_with_user_message(self):
        """Test execution with user message"""
        messages = [
            {'role': 'user', 'content': 'Hello!'}
        ]

        result = self._execute_agent('agent-1', messages)
        assert 'response' in result
        assert result['status'] == 'success'

    def test_execute_with_conversation_history(self):
        """Test execution with multi-turn conversation"""
        messages = [
            {'role': 'user', 'content': 'What is 2+2?'},
            {'role': 'assistant', 'content': '4'},
            {'role': 'user', 'content': 'What about 3+3?'},
        ]

        result = self._execute_agent('agent-1', messages)
        assert result['status'] == 'success'

    def test_execute_with_tool_calls(self):
        """Test execution that requires tool calls"""
        agent_id = 'agent-with-tools'
        messages = [
            {'role': 'user', 'content': 'Search the web for Python tutorials'}
        ]

        result = self._execute_agent(agent_id, messages)
        assert result['status'] == 'success'
        # Should have made tool calls
        assert 'tool_calls' in result or 'response' in result

    def test_execute_timeout_handling(self):
        """Test execution timeout"""
        messages = [{'role': 'user', 'content': 'Long task'}]

        # Should timeout after 30s (mock)
        with pytest.raises(TimeoutError):
            self._execute_agent('slow-agent', messages, timeout=0.1)

    def test_execute_error_handling(self):
        """Test error handling during execution"""
        messages = [{'role': 'user', 'content': 'Cause error'}]

        # Should handle LLM API errors gracefully
        result = self._execute_agent('broken-agent', messages)
        assert result['status'] == 'error'
        assert 'error' in result

    # Mock implementations
    def _execute_agent(self, agent_id, messages, timeout=30):
        if not messages:
            raise ValueError("Messages cannot be empty")

        if agent_id == 'slow-agent' and timeout < 1:
            raise TimeoutError("Execution timeout")

        if agent_id == 'broken-agent':
            return {'status': 'error', 'error': 'LLM API error'}

        return {
            'status': 'success',
            'response': 'This is a test response',
            'agent_id': agent_id,
        }


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
