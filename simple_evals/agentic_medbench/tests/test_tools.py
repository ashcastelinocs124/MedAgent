"""Tests for agentic_medbench tool definitions and registry."""

from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from simple_evals.agentic_medbench.tools import (
    TOOL_SCHEMAS,
    BaseTool,
    BrainGraphTool,
    DrugInteractionTool,
    PubMedTool,
    ToolRegistry,
    WebSearchTool,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

EXPECTED_TOOL_NAMES = frozenset(
    {"brain_graph", "pubmed_search", "drug_interaction_db", "web_search"}
)


def _validate_function_calling_schema(schema: dict) -> None:
    """Assert that *schema* follows the OpenAI function-calling format."""
    assert schema["type"] == "function"
    fn = schema["function"]
    assert isinstance(fn["name"], str) and fn["name"]
    assert isinstance(fn["description"], str) and fn["description"]
    params = fn["parameters"]
    assert params["type"] == "object"
    assert isinstance(params["properties"], dict)
    assert isinstance(params.get("required", []), list)


# ---------------------------------------------------------------------------
# TOOL_SCHEMAS
# ---------------------------------------------------------------------------


class TestToolSchemas:
    """Validate the module-level TOOL_SCHEMAS list."""

    def test_has_four_schemas(self):
        assert len(TOOL_SCHEMAS) == 4

    def test_each_schema_has_correct_structure(self):
        for schema in TOOL_SCHEMAS:
            _validate_function_calling_schema(schema)

    def test_all_tool_names_present(self):
        names = {s["function"]["name"] for s in TOOL_SCHEMAS}
        assert names == EXPECTED_TOOL_NAMES

    def test_schemas_are_json_serializable(self):
        """Schemas must be sendable to an API as JSON."""
        serialized = json.dumps(TOOL_SCHEMAS)
        roundtripped = json.loads(serialized)
        assert roundtripped == TOOL_SCHEMAS


# ---------------------------------------------------------------------------
# ToolRegistry
# ---------------------------------------------------------------------------


class TestToolRegistry:
    """Tests for the ToolRegistry lookup and execution layer."""

    def setup_method(self):
        self.registry = ToolRegistry()

    # -- get() ---------------------------------------------------------------

    def test_get_returns_correct_tool_instances(self):
        for name in EXPECTED_TOOL_NAMES:
            tool = self.registry.get(name)
            assert tool is not None
            assert isinstance(tool, BaseTool)
            assert tool.name == name

    def test_get_unknown_tool_returns_none(self):
        assert self.registry.get("nonexistent_tool") is None

    # -- get_schemas() -------------------------------------------------------

    def test_get_schemas_all(self):
        schemas = self.registry.get_schemas()
        assert len(schemas) == 4
        names = {s["function"]["name"] for s in schemas}
        assert names == EXPECTED_TOOL_NAMES

    def test_get_schemas_subset(self):
        subset = ["pubmed_search", "brain_graph"]
        schemas = self.registry.get_schemas(subset)
        assert len(schemas) == 2
        names = {s["function"]["name"] for s in schemas}
        assert names == set(subset)

    def test_get_schemas_empty_list(self):
        schemas = self.registry.get_schemas([])
        assert schemas == []

    def test_get_schemas_ignores_unknown(self):
        schemas = self.registry.get_schemas(["pubmed_search", "bogus"])
        assert len(schemas) == 1
        assert schemas[0]["function"]["name"] == "pubmed_search"

    # -- execute() -----------------------------------------------------------

    def test_execute_unknown_tool_returns_error_string(self):
        result = self.registry.execute("no_such_tool", {})
        assert "error" in result.lower()

    def test_execute_delegates_to_tool_call(self):
        """execute() should call the tool's call() method with the arguments."""
        mock_tool = MagicMock(spec=BaseTool)
        mock_tool.name = "mock_tool"
        mock_tool.call.return_value = "mock result"
        self.registry._tools["mock_tool"] = mock_tool

        result = self.registry.execute("mock_tool", {"q": "test"})
        mock_tool.call.assert_called_once_with({"q": "test"})
        assert result == "mock result"


# ---------------------------------------------------------------------------
# BrainGraphTool
# ---------------------------------------------------------------------------


class TestBrainGraphTool:
    """Tests for BrainGraphTool loading real brain markdown files."""

    def setup_method(self):
        self.tool = BrainGraphTool()

    def test_name_and_schema(self):
        assert self.tool.name == "brain_graph"
        schema = self.tool.schema()
        _validate_function_calling_schema(schema)
        assert "category" in schema["function"]["parameters"]["properties"]

    def test_load_heart_blood_vessels(self):
        """Load a real brain category file and verify content is returned."""
        result = self.tool.call({"category": "heart_blood_vessels"})
        assert "Heart & Blood Vessels" in result
        assert "Hypertension" in result

    def test_load_general_rules(self):
        """Loading 'general_rules' should return the general rules file."""
        result = self.tool.call({"category": "general_rules"})
        assert "General Rules" in result
        assert "Source Verification" in result

    def test_unknown_category_returns_error(self):
        result = self.tool.call({"category": "nonexistent_category_xyz"})
        assert "not found" in result.lower() or "error" in result.lower()

    def test_list_categories(self):
        """Passing 'list' as category should return available categories."""
        result = self.tool.call({"category": "list"})
        assert "heart_blood_vessels" in result
        assert "mental_health" in result


# ---------------------------------------------------------------------------
# PubMedTool
# ---------------------------------------------------------------------------


class TestPubMedTool:
    """Tests for PubMedTool (uses mocked HTTP to avoid live API calls)."""

    def setup_method(self):
        self.tool = PubMedTool()

    def test_name_and_schema(self):
        assert self.tool.name == "pubmed_search"
        schema = self.tool.schema()
        _validate_function_calling_schema(schema)
        props = schema["function"]["parameters"]["properties"]
        assert "query" in props
        assert "max_results" in props

    @patch("simple_evals.agentic_medbench.tools.urlopen")
    def test_call_returns_articles(self, mock_urlopen):
        """Mock the NCBI E-utilities responses to test parsing logic."""
        # esearch response
        esearch_response = MagicMock()
        esearch_response.read.return_value = json.dumps(
            {"esearchresult": {"idlist": ["12345", "67890"]}}
        ).encode()
        esearch_response.__enter__ = lambda s: s
        esearch_response.__exit__ = MagicMock(return_value=False)

        # esummary response
        esummary_response = MagicMock()
        esummary_response.read.return_value = json.dumps(
            {
                "result": {
                    "uids": ["12345", "67890"],
                    "12345": {
                        "uid": "12345",
                        "title": "Aspirin and Cardiovascular Risk",
                        "source": "NEJM",
                        "pubdate": "2024",
                    },
                    "67890": {
                        "uid": "67890",
                        "title": "Metformin Outcomes Study",
                        "source": "Lancet",
                        "pubdate": "2023",
                    },
                }
            }
        ).encode()
        esummary_response.__enter__ = lambda s: s
        esummary_response.__exit__ = MagicMock(return_value=False)

        mock_urlopen.side_effect = [esearch_response, esummary_response]

        result = self.tool.call({"query": "aspirin cardiovascular"})
        assert "Aspirin and Cardiovascular Risk" in result
        assert "12345" in result
        assert "Metformin Outcomes Study" in result

    @patch("simple_evals.agentic_medbench.tools.urlopen")
    def test_call_handles_empty_results(self, mock_urlopen):
        """Empty search results should return a meaningful message."""
        esearch_response = MagicMock()
        esearch_response.read.return_value = json.dumps(
            {"esearchresult": {"idlist": []}}
        ).encode()
        esearch_response.__enter__ = lambda s: s
        esearch_response.__exit__ = MagicMock(return_value=False)

        mock_urlopen.return_value = esearch_response

        result = self.tool.call({"query": "xyznonexistentquery"})
        assert "no results" in result.lower() or "0" in result

    @patch("simple_evals.agentic_medbench.tools.urlopen")
    def test_call_handles_network_error(self, mock_urlopen):
        """Network errors should be caught and returned as an error string."""
        mock_urlopen.side_effect = Exception("Connection refused")
        result = self.tool.call({"query": "aspirin"})
        assert "error" in result.lower()


# ---------------------------------------------------------------------------
# DrugInteractionTool
# ---------------------------------------------------------------------------


class TestDrugInteractionTool:
    """Tests for DrugInteractionTool (uses mocked HTTP)."""

    def setup_method(self):
        self.tool = DrugInteractionTool()

    def test_name_and_schema(self):
        assert self.tool.name == "drug_interaction_db"
        schema = self.tool.schema()
        _validate_function_calling_schema(schema)
        props = schema["function"]["parameters"]["properties"]
        assert "drug_name" in props
        required = schema["function"]["parameters"]["required"]
        assert "drug_name" in required

    @patch("simple_evals.agentic_medbench.tools.urlopen")
    def test_call_returns_interaction_data(self, mock_urlopen):
        """Mock OpenFDA response with drug interaction info."""
        fda_response = MagicMock()
        fda_response.read.return_value = json.dumps(
            {
                "results": [
                    {
                        "drug_interactions": [
                            "Do not take with warfarin. Increased bleeding risk."
                        ]
                    }
                ]
            }
        ).encode()
        fda_response.__enter__ = lambda s: s
        fda_response.__exit__ = MagicMock(return_value=False)

        mock_urlopen.return_value = fda_response

        result = self.tool.call({"drug_name": "aspirin"})
        assert "warfarin" in result.lower() or "interaction" in result.lower()

    @patch("simple_evals.agentic_medbench.tools.urlopen")
    def test_truncation_of_long_results(self, mock_urlopen):
        """Results longer than 500 chars should be truncated."""
        long_text = "A" * 1000
        fda_response = MagicMock()
        fda_response.read.return_value = json.dumps(
            {"results": [{"drug_interactions": [long_text]}]}
        ).encode()
        fda_response.__enter__ = lambda s: s
        fda_response.__exit__ = MagicMock(return_value=False)

        mock_urlopen.return_value = fda_response

        result = self.tool.call({"drug_name": "aspirin"})
        # Should be truncated to approximately 500 chars + truncation indicator
        assert len(result) <= 600  # some room for the truncation marker

    @patch("simple_evals.agentic_medbench.tools.urlopen")
    def test_call_handles_network_error(self, mock_urlopen):
        mock_urlopen.side_effect = Exception("timeout")
        result = self.tool.call({"drug_name": "aspirin"})
        assert "error" in result.lower()


# ---------------------------------------------------------------------------
# WebSearchTool
# ---------------------------------------------------------------------------


class TestWebSearchTool:
    """Tests for the simulated WebSearchTool."""

    def setup_method(self):
        self.tool = WebSearchTool()

    def test_name_and_schema(self):
        assert self.tool.name == "web_search"
        schema = self.tool.schema()
        _validate_function_calling_schema(schema)
        assert "query" in schema["function"]["parameters"]["properties"]

    def test_call_returns_placeholder(self):
        """WebSearchTool should return a simulated/placeholder result."""
        result = self.tool.call({"query": "aspirin side effects"})
        assert isinstance(result, str)
        assert len(result) > 0
        # Should mention it's simulated or contain some placeholder content
        assert "simulated" in result.lower() or "placeholder" in result.lower() or "web search" in result.lower()

    def test_call_includes_query(self):
        """The placeholder result should echo back the query for context."""
        result = self.tool.call({"query": "diabetes management tips"})
        assert "diabetes management tips" in result.lower() or "diabetes" in result.lower()


# ---------------------------------------------------------------------------
# NCBIRateLimiter
# ---------------------------------------------------------------------------


def test_ncbi_rate_limiter_throttles_concurrent_requests():
    """Rate limiter should prevent more than max_per_second requests."""
    from simple_evals.agentic_medbench.tools import NCBIRateLimiter

    limiter = NCBIRateLimiter(max_per_second=5)
    timestamps: list[float] = []

    def make_request():
        limiter.acquire()
        timestamps.append(time.time())

    threads = [threading.Thread(target=make_request) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # 10 requests at 5/s should take at least 1 second
    duration = max(timestamps) - min(timestamps)
    assert duration >= 0.9, f"Expected >= 0.9s, got {duration:.2f}s"


def test_pubmed_tool_includes_api_key_when_set():
    """PubMed requests should include api_key param when NCBI_API_KEY is set."""
    from simple_evals.agentic_medbench.tools import PubMedTool

    tool = PubMedTool()
    captured_urls: list[str] = []

    def mock_urlopen(request, **kwargs):
        captured_urls.append(
            request.full_url if hasattr(request, "full_url") else str(request)
        )

        class MockResp:
            def read(self):
                return b'{"esearchresult": {"idlist": []}}'

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

        return MockResp()

    with patch.dict("os.environ", {"NCBI_API_KEY": "test_key_123"}):
        with patch("simple_evals.agentic_medbench.tools.urlopen", mock_urlopen):
            tool.call({"query": "aspirin"})

    assert any("api_key=test_key_123" in url for url in captured_urls), \
        f"API key not found in URLs: {captured_urls}"
