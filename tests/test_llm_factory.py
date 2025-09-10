import os
import pytest
from app.llm.factory import get_llm
from app.llm.base import LLMError


def test_unknown_provider_raises():
    with pytest.raises(LLMError):
        get_llm(provider="unknown_provider")


