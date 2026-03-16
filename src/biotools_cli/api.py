from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Any, Iterable, Mapping
import urllib.error
import urllib.parse
import urllib.request

from . import __version__

DEFAULT_BASE_URL = "https://bio.tools/api"
DEFAULT_TIMEOUT = 30.0
LIST_FORMATS = ("json", "api")
DETAIL_FORMATS = ("json", "xml", "api")
SORT_OPTIONS = ("lastUpdate", "additionDate", "name", "score")
ORDER_OPTIONS = ("desc", "asc")
USED_TERM_ATTRIBUTES = ("name", "topic", "functionName", "input", "output", "credits", "all")
USED_TERM_ATTRIBUTE_ALIASES = {
    "function-name": "functionName",
    "functionname": "functionName",
    "function": "functionName",
    "operation": "functionName",
    "credit": "credits",
}
USED_TERM_ENDPOINTS = {
    "name": "name",
    "topic": "topic",
    "functionName": "operation",
    "input": "input",
    "output": "output",
    "credits": "credit",
    "all": "all",
}
USED_TERM_ATTRIBUTE_CASE_MAP = {attribute.lower(): attribute for attribute in USED_TERM_ATTRIBUTES}

_WORD_PATTERN = re.compile(r"[A-Z]+(?=[A-Z][a-z]|$)|[A-Z]?[a-z]+|\d+")


class ApiError(RuntimeError):
    """Raised when the bio.tools API request fails."""


@dataclass(frozen=True)
class ToolFilterSpec:
    api_name: str
    description: str
    must_quote: bool = False

    @property
    def option_name(self) -> str:
        return camel_to_kebab(self.api_name)


TOOL_FILTERS = (
    ToolFilterSpec("biotoolsID", "Search by bio.tools tool ID."),
    ToolFilterSpec("name", "Search by tool name."),
    ToolFilterSpec("homepage", "Search by exact homepage URL.", must_quote=True),
    ToolFilterSpec("description", "Search within tool descriptions."),
    ToolFilterSpec("version", "Search by exact tool version.", must_quote=True),
    ToolFilterSpec("topic", "Search by EDAM topic term."),
    ToolFilterSpec("topicID", "Search by exact EDAM topic ID or URI.", must_quote=True),
    ToolFilterSpec("function", "Fuzzy search across tool function fields."),
    ToolFilterSpec("operation", "Search by EDAM operation term."),
    ToolFilterSpec("operationID", "Search by exact EDAM operation ID or URI.", must_quote=True),
    ToolFilterSpec("dataType", "Search by EDAM data term across input and output."),
    ToolFilterSpec("dataTypeID", "Search by exact EDAM data ID or URI.", must_quote=True),
    ToolFilterSpec("dataFormat", "Search by EDAM format term across input and output."),
    ToolFilterSpec("dataFormatID", "Search by exact EDAM format ID or URI.", must_quote=True),
    ToolFilterSpec("input", "Search across input data and format terms."),
    ToolFilterSpec("inputID", "Search by exact input data or format ID.", must_quote=True),
    ToolFilterSpec("inputDataType", "Search by input EDAM data term."),
    ToolFilterSpec("inputDataTypeID", "Search by exact input EDAM data ID.", must_quote=True),
    ToolFilterSpec("inputDataFormat", "Search by input EDAM format term."),
    ToolFilterSpec("inputDataFormatID", "Search by exact input EDAM format ID.", must_quote=True),
    ToolFilterSpec("output", "Search across output data and format terms."),
    ToolFilterSpec("outputID", "Search by exact output data or format ID.", must_quote=True),
    ToolFilterSpec("outputDataType", "Search by output EDAM data term."),
    ToolFilterSpec("outputDataTypeID", "Search by exact output EDAM data ID.", must_quote=True),
    ToolFilterSpec("outputDataFormat", "Search by output EDAM format term."),
    ToolFilterSpec("outputDataFormatID", "Search by exact output EDAM format ID.", must_quote=True),
    ToolFilterSpec("toolType", "Search by exact tool type."),
    ToolFilterSpec("collectionID", "Search by exact tool collection."),
    ToolFilterSpec("maturity", "Search by exact maturity level."),
    ToolFilterSpec("operatingSystem", "Search by exact operating system."),
    ToolFilterSpec("language", "Search by exact programming language."),
    ToolFilterSpec("cost", "Search by exact cost."),
    ToolFilterSpec("license", "Search by software or data license."),
    ToolFilterSpec("accessibility", "Search by exact accessibility value."),
    ToolFilterSpec("credit", "Search across credited entity fields."),
    ToolFilterSpec("creditName", "Search by exact credited entity name."),
    ToolFilterSpec("creditTypeRole", "Search by exact credited entity role."),
    ToolFilterSpec("creditTypeEntity", "Search by exact credited entity type."),
    ToolFilterSpec("creditOrcidID", "Search by exact credited ORCID iD.", must_quote=True),
    ToolFilterSpec("publication", "Search across publication identifiers and metadata."),
    ToolFilterSpec("publicationID", "Search by exact DOI, PMID, or PMCID.", must_quote=True),
    ToolFilterSpec("publicationType", "Search by exact publication type."),
    ToolFilterSpec("publicationVersion", "Search by exact publication-associated tool version.", must_quote=True),
    ToolFilterSpec("link", "Search across general links."),
    ToolFilterSpec("linkType", "Search by exact link type."),
    ToolFilterSpec("documentation", "Search across documentation links."),
    ToolFilterSpec("documentationType", "Search by exact documentation type."),
    ToolFilterSpec("download", "Search across download links."),
    ToolFilterSpec("downloadType", "Search by exact download type."),
    ToolFilterSpec("downloadVersion", "Search by exact download version.", must_quote=True),
    ToolFilterSpec("otherID", "Search across alternate tool identifiers."),
    ToolFilterSpec("otherIDValue", "Search by exact alternate identifier value.", must_quote=True),
    ToolFilterSpec("otherIDType", "Search by exact alternate identifier type."),
    ToolFilterSpec("otherIDVersion", "Search by exact alternate identifier version.", must_quote=True),
    ToolFilterSpec("domain", "Filter results to a domain."),
)

QUOTE_REQUIRED_FILTERS = {spec.api_name for spec in TOOL_FILTERS if spec.must_quote}


def camel_to_kebab(value: str) -> str:
    return "-".join(token.lower() for token in _WORD_PATTERN.findall(value))


def quote_for_api(value: Any) -> str:
    text = str(value)
    if len(text) >= 2 and text.startswith('"') and text.endswith('"'):
        return text
    return f'"{text}"'


def normalize_used_term_attribute(value: str) -> str:
    candidate = value.strip()
    lower_candidate = candidate.lower()
    normalized = USED_TERM_ATTRIBUTE_ALIASES.get(candidate)
    if normalized is None:
        normalized = USED_TERM_ATTRIBUTE_ALIASES.get(lower_candidate)
    if normalized is None:
        normalized = USED_TERM_ATTRIBUTE_CASE_MAP.get(lower_candidate, candidate)
    if normalized not in USED_TERM_ATTRIBUTES:
        choices = ", ".join(sorted(USED_TERM_ATTRIBUTES))
        raise ValueError(f"Invalid used-terms attribute '{value}'. Expected one of: {choices}.")
    return normalized


def resolve_used_term_endpoint(value: str) -> str:
    normalized = normalize_used_term_attribute(value)
    return USED_TERM_ENDPOINTS[normalized]


def normalize_tool_params(
    params: Mapping[str, Any],
    *,
    exact_keys: Iterable[str] = (),
) -> dict[str, str]:
    exact = set(exact_keys)
    normalized: dict[str, str] = {}

    for key, value in params.items():
        if value is None:
            continue

        text = str(value)
        if key in QUOTE_REQUIRED_FILTERS or key in exact:
            text = quote_for_api(text)

        normalized[key] = text

    return normalized


@dataclass(frozen=True)
class ResponsePayload:
    url: str
    content_type: str
    text: str

    def json(self) -> Any:
        return json.loads(self.text)


class BioToolsClient:
    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        *,
        user_agent: str | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.user_agent = user_agent or f"biotools-cli/{__version__}"

    def _build_url(self, path: str, params: Mapping[str, Any] | None = None) -> str:
        url = f"{self.base_url}/{path.lstrip('/')}"
        if not params:
            return url

        query = urllib.parse.urlencode([(key, str(value)) for key, value in params.items()], doseq=True)
        if not query:
            return url

        return f"{url}?{query}"

    def _request(self, path: str, params: Mapping[str, Any] | None = None) -> ResponsePayload:
        url = self._build_url(path, params)
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": self.user_agent,
                "Accept": "application/json, application/xml, text/plain;q=0.8, */*;q=0.1",
            },
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw = response.read()
                charset = response.headers.get_content_charset() or "utf-8"
                text = raw.decode(charset, errors="replace")
                return ResponsePayload(url=url, content_type=response.headers.get("Content-Type", ""), text=text)
        except urllib.error.HTTPError as error:
            charset = error.headers.get_content_charset() if error.headers else None
            body = error.read().decode(charset or "utf-8", errors="replace").strip()
            detail = body or error.reason
            raise ApiError(f"HTTP {error.code} for {url}: {detail}") from error
        except urllib.error.URLError as error:
            raise ApiError(f"Request failed for {url}: {error.reason}") from error

    def _request_json(self, path: str, params: Mapping[str, Any] | None = None) -> Any:
        payload = self._request(path, params)
        try:
            return payload.json()
        except json.JSONDecodeError as error:
            raise ApiError(f"Expected JSON response for {payload.url}, but the body could not be decoded.") from error

    def _request_formatted(self, path: str, response_format: str = "json") -> Any:
        params = {"format": response_format} if response_format else None
        if response_format == "json":
            return self._request_json(path, params)
        return self._request(path, params).text

    def list_tools(self, params: Mapping[str, Any], *, fetch_all: bool = False) -> Any:
        response_format = str(params.get("format", "json"))
        if fetch_all and response_format != "json":
            raise ValueError("Fetching all pages requires '--format json'.")

        if not fetch_all:
            if response_format == "json":
                return self._request_json("tool/", params)
            return self._request("tool/", params).text

        next_page = int(params.get("page", 1))
        merged: dict[str, Any] | None = None
        items: list[Any] = []
        pages_fetched = 0

        while True:
            page_params = dict(params)
            page_params["page"] = str(next_page)
            page_data = self._request_json("tool/", page_params)
            if not isinstance(page_data, dict) or "list" not in page_data:
                raise ApiError("Unexpected response while aggregating paginated tool results.")

            if merged is None:
                merged = {key: value for key, value in page_data.items() if key != "list"}

            pages_fetched += 1
            items.extend(page_data.get("list", []))

            next_link = page_data.get("next")
            if not next_link:
                break

            next_page = self._next_page_number(next_link, default=next_page + 1)

        assert merged is not None
        merged["previous"] = None
        merged["next"] = None
        merged["pages_fetched"] = pages_fetched
        merged["list"] = items
        return merged

    def get_tool(self, tool_id: str, *, response_format: str = "json") -> Any:
        safe_id = urllib.parse.quote(tool_id, safe="")
        return self._request_formatted(f"tool/{safe_id}/", response_format=response_format)

    def list_used_terms(self, attribute: str, *, response_format: str = "json") -> Any:
        safe_attribute = urllib.parse.quote(attribute, safe="")
        return self._request_formatted(f"used-terms/{safe_attribute}/", response_format=response_format)

    def get_stats(self) -> Any:
        return self._request_json("stats")

    def list_domains(self) -> Any:
        return self._request_json("d/")

    def get_domain(self, name: str, *, response_format: str = "json") -> Any:
        safe_name = urllib.parse.quote(name, safe="")
        return self._request_formatted(f"d/{safe_name}/", response_format=response_format)

    @staticmethod
    def _next_page_number(next_link: str, *, default: int) -> int:
        parsed = urllib.parse.urlparse(next_link)
        query = urllib.parse.parse_qs(parsed.query)
        try:
            return int(query.get("page", [str(default)])[0])
        except (TypeError, ValueError):
            return default
