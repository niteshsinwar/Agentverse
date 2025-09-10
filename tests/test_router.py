from app.agents.router import Router


class DummyOrchestrator:
    pass


def test_parse_single_agent_with_content():
    r = Router(DummyOrchestrator())
    agent_key, content = r.parse("@agent_1 Hello world")
    assert agent_key == "agent_1"
    assert content == "Hello world"


def test_parse_single_agent_multiple_mentions_same():
    r = Router(DummyOrchestrator())
    agent_key, content = r.parse("@a do this @a then that")
    assert agent_key == "a"
    assert content == "do this  then that".strip()


def test_parse_multiple_different_agents_returns_none():
    r = Router(DummyOrchestrator())
    assert r.parse("@a do this @b then that") is None


