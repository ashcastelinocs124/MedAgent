"""Tool definitions for Agentic MedBench evaluation.

Provides the tools that agents can invoke during medical QA evaluation:
BrainGraphTool, PubMedTool, DrugInteractionTool, and WebSearchTool.

Each tool exposes an OpenAI function-calling schema and a ``call()`` method
that executes the tool logic and returns a plain-text result string.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time as _time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus, urlencode
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Brain directory — resolved relative to project root
# ---------------------------------------------------------------------------

_BRAIN_DIR: Path = Path(__file__).resolve().parent.parent.parent / "brain"

# ---------------------------------------------------------------------------
# Base tool
# ---------------------------------------------------------------------------


class BaseTool(ABC):
    """Abstract base class for all evaluation tools.

    Subclasses must define ``name``, ``description``, ``parameters``, and
    implement the ``call`` method.
    """

    name: str
    description: str
    parameters: dict[str, Any]  # JSON-Schema "parameters" object

    @abstractmethod
    def call(self, arguments: dict[str, Any]) -> str:
        """Execute the tool with the given *arguments* and return a result string."""

    def schema(self) -> dict[str, Any]:
        """Return the OpenAI function-calling schema for this tool."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


# ---------------------------------------------------------------------------
# BrainGraphTool
# ---------------------------------------------------------------------------


class BrainGraphTool(BaseTool):
    """Load brain category markdown files or list available categories.

    The brain directory lives at the project root under ``brain/``.  Passing
    ``category="list"`` returns all available category slugs.  Passing
    ``category="general_rules"`` loads the cross-category general rules.
    Any other value is treated as a category slug and loads
    ``brain/categories/{slug}.md``.
    """

    name = "brain_graph"
    description = (
        "Look up health-domain knowledge from the brain knowledge base. "
        "Pass a category slug (e.g. 'heart_blood_vessels', 'mental_health') "
        "to retrieve its content, 'general_rules' for cross-category rules, "
        "or 'list' to see all available categories."
    )
    parameters: dict[str, Any] = {
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
                "description": (
                    "Category slug to load (e.g. 'heart_blood_vessels'), "
                    "'general_rules' for common patterns, or 'list' to "
                    "enumerate available categories."
                ),
            },
        },
        "required": ["category"],
    }

    def __init__(self, brain_dir: Path | None = None) -> None:
        self._brain_dir = brain_dir or _BRAIN_DIR

    def call(self, arguments: dict[str, Any]) -> str:
        category: str = arguments.get("category", "").strip()
        if not category:
            return "Error: 'category' argument is required."

        # List mode
        if category == "list":
            return self._list_categories()

        # General rules
        if category == "general_rules":
            path = self._brain_dir / "general_rules.md"
        else:
            path = self._brain_dir / "categories" / f"{category}.md"

        if not path.is_file():
            available = self._list_categories()
            return (
                f"Error: Category '{category}' not found. "
                f"Available categories:\n{available}"
            )

        try:
            content = path.read_text(encoding="utf-8")
            return content
        except Exception as exc:
            return f"Error reading '{category}': {exc}"

    def _list_categories(self) -> str:
        categories_dir = self._brain_dir / "categories"
        if not categories_dir.is_dir():
            return "Error: brain/categories directory not found."
        slugs = sorted(
            p.stem for p in categories_dir.glob("*.md") if p.is_file()
        )
        return "Available categories:\n" + "\n".join(f"  - {s}" for s in slugs)


# ---------------------------------------------------------------------------
# NCBI rate limiter
# ---------------------------------------------------------------------------


class NCBIRateLimiter:
    """Thread-safe rate limiter for NCBI E-utilities API.

    NCBI allows 3 requests/second without an API key, 10 with one.
    Default ``max_per_second=8.0`` provides a safety margin when an API key
    is configured.
    """

    def __init__(self, max_per_second: float = 8.0) -> None:
        self._min_interval = 1.0 / max_per_second
        self._lock = threading.Lock()
        self._last_request = 0.0

    def acquire(self) -> None:
        """Block until a request slot is available."""
        with self._lock:
            now = _time.time()
            elapsed = now - self._last_request
            if elapsed < self._min_interval:
                _time.sleep(self._min_interval - elapsed)
            self._last_request = _time.time()


_ncbi_limiter = NCBIRateLimiter()


# ---------------------------------------------------------------------------
# PubMedTool
# ---------------------------------------------------------------------------

_NCBI_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


class PubMedTool(BaseTool):
    """Search PubMed via NCBI E-utilities and return article summaries."""

    name = "pubmed_search"
    description = (
        "Search PubMed for biomedical literature. Returns article titles, "
        "PMIDs, journal names, and publication dates."
    )
    parameters: dict[str, Any] = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "PubMed search query (e.g. 'aspirin cardiovascular risk').",
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results to return (default 5).",
            },
        },
        "required": ["query"],
    }

    def call(self, arguments: dict[str, Any]) -> str:
        query: str = arguments.get("query", "").strip()
        if not query:
            return "Error: 'query' argument is required."
        max_results: int = int(arguments.get("max_results", 5))

        # Include NCBI API key when available (raises rate limit 3 -> 10 req/s)
        api_key = os.environ.get("NCBI_API_KEY", "")

        try:
            # Step 1: esearch — get PMIDs
            search_dict: dict[str, str | int] = {
                "db": "pubmed",
                "term": query,
                "retmax": max_results,
                "retmode": "json",
            }
            if api_key:
                search_dict["api_key"] = api_key
            search_params = urlencode(search_dict)
            search_url = f"{_NCBI_BASE}/esearch.fcgi?{search_params}"
            _ncbi_limiter.acquire()
            with urlopen(Request(search_url), timeout=15) as resp:
                search_data = json.loads(resp.read())

            id_list: list[str] = search_data.get("esearchresult", {}).get(
                "idlist", []
            )
            if not id_list:
                return f"PubMed search for '{query}': No results found."

            # Step 2: esummary — get article metadata
            summary_dict: dict[str, str | int] = {
                "db": "pubmed",
                "id": ",".join(id_list),
                "retmode": "json",
            }
            if api_key:
                summary_dict["api_key"] = api_key
            summary_params = urlencode(summary_dict)
            summary_url = f"{_NCBI_BASE}/esummary.fcgi?{summary_params}"
            _ncbi_limiter.acquire()
            with urlopen(Request(summary_url), timeout=15) as resp:
                summary_data = json.loads(resp.read())

            results = summary_data.get("result", {})
            articles: list[str] = []
            for uid in id_list:
                article = results.get(uid, {})
                title = article.get("title", "Unknown title")
                source = article.get("source", "Unknown journal")
                pubdate = article.get("pubdate", "Unknown date")
                articles.append(
                    f"- PMID {uid}: {title} ({source}, {pubdate})"
                )

            header = f"PubMed results for '{query}' ({len(articles)} articles):"
            return header + "\n" + "\n".join(articles)

        except Exception as exc:
            logger.warning("PubMedTool error: %s", exc)
            return f"Error searching PubMed: {exc}"


# ---------------------------------------------------------------------------
# DrugInteractionTool
# ---------------------------------------------------------------------------

_OPENFDA_BASE = "https://api.fda.gov/drug/label.json"
_MAX_RESULT_CHARS = 500


class DrugInteractionTool(BaseTool):
    """Query OpenFDA for drug interaction information."""

    name = "drug_interaction_db"
    description = (
        "Look up drug interaction data from the FDA drug label database. "
        "Returns interaction warnings and contraindications."
    )
    parameters: dict[str, Any] = {
        "type": "object",
        "properties": {
            "drug_name": {
                "type": "string",
                "description": "Primary drug name to look up (e.g. 'aspirin').",
            },
            "interacting_drug": {
                "type": "string",
                "description": (
                    "Optional second drug to check for specific interactions."
                ),
            },
        },
        "required": ["drug_name"],
    }

    def call(self, arguments: dict[str, Any]) -> str:
        drug_name: str = arguments.get("drug_name", "").strip()
        if not drug_name:
            return "Error: 'drug_name' argument is required."

        interacting_drug: str = arguments.get("interacting_drug", "").strip()

        try:
            # Build search query
            search_terms = [f'drug_interactions:"{drug_name}"']
            if interacting_drug:
                search_terms.append(f'drug_interactions:"{interacting_drug}"')

            params = urlencode(
                {
                    "search": "+AND+".join(search_terms),
                    "limit": 1,
                }
            )
            url = f"{_OPENFDA_BASE}?{params}"

            with urlopen(Request(url), timeout=15) as resp:
                data = json.loads(resp.read())

            results = data.get("results", [])
            if not results:
                return f"No interaction data found for '{drug_name}'."

            interactions = results[0].get("drug_interactions", [])
            if not interactions:
                return f"No specific interaction warnings found for '{drug_name}'."

            text = "\n".join(interactions)

            # Truncate if too long
            if len(text) > _MAX_RESULT_CHARS:
                text = text[:_MAX_RESULT_CHARS] + "... [truncated]"

            header = f"Drug interaction data for '{drug_name}'"
            if interacting_drug:
                header += f" with '{interacting_drug}'"
            return f"{header}:\n{text}"

        except Exception as exc:
            logger.warning("DrugInteractionTool error: %s", exc)
            return f"Error querying drug interactions: {exc}"


# ---------------------------------------------------------------------------
# WebSearchTool
# ---------------------------------------------------------------------------


class WebSearchTool(BaseTool):
    """Simulated web search tool for evaluation mode.

    Returns a placeholder result since no real web search API is used
    during benchmarking.
    """

    name = "web_search"
    description = (
        "Search the web for general health information. "
        "Returns a summary of relevant web results."
    )
    parameters: dict[str, Any] = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Web search query string.",
            },
        },
        "required": ["query"],
    }

    def call(self, arguments: dict[str, Any]) -> str:
        query: str = arguments.get("query", "").strip()
        if not query:
            return "Error: 'query' argument is required."

        return (
            f"[Simulated web search result for '{query}']\n"
            f"This is a placeholder response. In production, this tool "
            f"would return real web search results for the query: {query}. "
            f"For evaluation purposes, the agent should rely on PubMed "
            f"and the brain knowledge base for authoritative medical content."
        )


# ---------------------------------------------------------------------------
# TOOL_SCHEMAS — module-level list of all tool schemas
# ---------------------------------------------------------------------------

_ALL_TOOLS: list[BaseTool] = [
    BrainGraphTool(),
    PubMedTool(),
    DrugInteractionTool(),
    WebSearchTool(),
]

TOOL_SCHEMAS: list[dict[str, Any]] = [tool.schema() for tool in _ALL_TOOLS]


# ---------------------------------------------------------------------------
# ToolRegistry
# ---------------------------------------------------------------------------


class ToolRegistry:
    """Registry that maps tool names to tool instances.

    Provides lookup, schema retrieval, and execution in a single interface
    so callers do not need to manage individual tool objects.
    """

    def __init__(self, tools: list[BaseTool] | None = None) -> None:
        tool_list = tools if tools is not None else list(_ALL_TOOLS)
        self._tools: dict[str, BaseTool] = {t.name: t for t in tool_list}

    def get(self, name: str) -> BaseTool | None:
        """Return the tool with the given *name*, or ``None`` if not found."""
        return self._tools.get(name)

    def get_schemas(
        self, tool_names: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """Return OpenAI function-calling schemas for the requested tools.

        Args:
            tool_names: List of tool names to include.  If ``None``, return
                schemas for all registered tools.

        Returns:
            List of schema dicts in OpenAI function-calling format.
        """
        if tool_names is None:
            return [t.schema() for t in self._tools.values()]
        return [
            self._tools[name].schema()
            for name in tool_names
            if name in self._tools
        ]

    def execute(self, tool_name: str, arguments: dict[str, Any]) -> str:
        """Execute a tool by name and return the result string.

        Args:
            tool_name: Name of the tool to execute.
            arguments: Arguments to pass to the tool's ``call`` method.

        Returns:
            The tool's result string, or an error message if the tool is
            not found.
        """
        tool = self._tools.get(tool_name)
        if tool is None:
            return f"Error: Tool '{tool_name}' not found in registry."
        return tool.call(arguments)
