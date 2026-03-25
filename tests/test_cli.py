from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from biotools_cli.cli import build_tool_query, main


class BuildToolQueryTests(unittest.TestCase):
    def test_named_and_exact_filters_are_mapped(self) -> None:
        argv = [
            "tools",
            "--name",
            "signalp",
            "--homepage",
            "https://example.org/tool",
            "--exact",
            "biotoolsID=signalp",
        ]

        parser = __import__("biotools_cli.cli", fromlist=["build_parser"]).build_parser()
        args = parser.parse_args(argv)
        query = build_tool_query(args)

        self.assertEqual(query["name"], "signalp")
        self.assertEqual(query["homepage"], '"https://example.org/tool"')
        self.assertEqual(query["biotoolsID"], '"signalp"')


class MainTests(unittest.TestCase):
    def test_tool_command_prints_json(self) -> None:
        fake_payload = {"biotoolsID": "signalp"}

        with patch("biotools_cli.cli.BioToolsClient") as client_cls:
            client_cls.return_value.get_tool.return_value = fake_payload
            output = io.StringIO()
            with redirect_stdout(output):
                exit_code = main(["tool", "signalp"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(json.loads(output.getvalue()), fake_payload)

    def test_filters_command_lists_known_option(self) -> None:
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = main(["filters"])

        self.assertEqual(exit_code, 0)
        text = output.getvalue()
        self.assertIn("--biotools-id", text)
        self.assertIn("Supported tool search filters", text)


if __name__ == "__main__":
    unittest.main()
