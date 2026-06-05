import pytest
from unittest.mock import patch
from core.ai.tools import get_available_tools

class TestAiGaps:

    def test_get_available_tools_coverage(self):
        # Strictly for coverage of tools.py:53 if it was somehow missed
        tools = get_available_tools()
        assert isinstance(tools, list)
        assert len(tools) > 0
        assert tools[0]["function"]["name"] == "propose_fix"
