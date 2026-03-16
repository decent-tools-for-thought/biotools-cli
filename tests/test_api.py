from __future__ import annotations

import unittest
from unittest.mock import patch

from biotools_cli.api import (
    BioToolsClient,
    normalize_tool_params,
    normalize_used_term_attribute,
    resolve_used_term_endpoint,
)


class NormalizeToolParamsTests(unittest.TestCase):
    def test_quotes_required_and_exact_parameters(self) -> None:
        params = normalize_tool_params(
            {
                "homepage": "https://example.org/tool",
                "name": "SignalP",
                "topicID": "operation_2403",
            },
            exact_keys={"name"},
        )

        self.assertEqual(params["homepage"], '"https://example.org/tool"')
        self.assertEqual(params["topicID"], '"operation_2403"')
        self.assertEqual(params["name"], '"SignalP"')

    def test_used_term_alias_is_normalized(self) -> None:
        self.assertEqual(normalize_used_term_attribute("function-name"), "functionName")

    def test_used_term_endpoint_matches_live_api(self) -> None:
        self.assertEqual(resolve_used_term_endpoint("function-name"), "operation")
        self.assertEqual(resolve_used_term_endpoint("credit"), "credit")


class ClientTests(unittest.TestCase):
    def test_build_url_encodes_query_string(self) -> None:
        client = BioToolsClient()
        url = client._build_url(
            "tool/",
            {
                "name": "signalp",
                "topicID": '"operation_2403"',
            },
        )

        self.assertEqual(
            url,
            "https://bio.tools/api/tool/?name=signalp&topicID=%22operation_2403%22",
        )

    def test_list_tools_fetch_all_merges_pages(self) -> None:
        client = BioToolsClient()
        pages = [
            {
                "count": 3,
                "previous": None,
                "next": "https://bio.tools/api/tool/?page=2",
                "list": [{"biotoolsID": "a"}, {"biotoolsID": "b"}],
            },
            {
                "count": 3,
                "previous": "https://bio.tools/api/tool/?page=1",
                "next": None,
                "list": [{"biotoolsID": "c"}],
            },
        ]

        with patch.object(client, "_request_json", side_effect=pages):
            merged = client.list_tools({"format": "json", "page": 1}, fetch_all=True)

        self.assertEqual(merged["count"], 3)
        self.assertEqual(merged["pages_fetched"], 2)
        self.assertEqual([item["biotoolsID"] for item in merged["list"]], ["a", "b", "c"])


if __name__ == "__main__":
    unittest.main()
