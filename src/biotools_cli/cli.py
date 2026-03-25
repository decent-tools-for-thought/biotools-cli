from __future__ import annotations

import argparse
import json
import sys
import textwrap
from collections.abc import Sequence
from typing import Any

from . import __version__
from .api import (
    DEFAULT_BASE_URL,
    DEFAULT_TIMEOUT,
    DETAIL_FORMATS,
    LIST_FORMATS,
    ORDER_OPTIONS,
    SORT_OPTIONS,
    TOOL_FILTERS,
    USED_TERM_ATTRIBUTES,
    ApiError,
    BioToolsClient,
    normalize_tool_params,
    resolve_used_term_endpoint,
)

_EXAMPLES = textwrap.dedent(
    """\
    examples:
      biotools tools --name signalp --sort name --order asc
      biotools tools --operation "Sequence analysis" --input-data-type "Protein sequence"
      biotools tools --all --q blast --per-page 100
      biotools tools --exact biotoolsID=signalp
      biotools tool signalp
      biotools terms function-name
      biotools stats
      biotools domains
      biotools domain proteomics
      biotools filters
    """
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="biotools",
        description="Read-only command line client for the bio.tools informative API endpoints.",
        epilog=_EXAMPLES,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        allow_abbrev=False,
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    common = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
    common.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help="Bio.tools API base URL. Default: %(default)s",
    )
    common.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        help="HTTP timeout in seconds. Default: %(default)s",
    )
    common.add_argument(
        "--compact",
        action="store_true",
        help="Print JSON on one line instead of pretty-printing it.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    tools_parser = subparsers.add_parser(
        "tools",
        parents=[common],
        help="List and search tools",
        description="List and search bio.tools entries.",
        epilog="Use 'biotools filters' to see all supported tool search filters.",
        allow_abbrev=False,
    )
    tools_parser.add_argument(
        "--page", type=int, default=1, help="Result page number. Default: %(default)s"
    )
    tools_parser.add_argument(
        "--per-page", type=int, default=50, help="Result page size. Default: %(default)s"
    )
    tools_parser.add_argument(
        "--format",
        choices=LIST_FORMATS,
        default="json",
        help="Response format. Default: %(default)s",
    )
    tools_parser.add_argument("--q", help="Full-text query across all indexed attributes.")
    tools_parser.add_argument(
        "--sort",
        choices=SORT_OPTIONS,
        default="lastUpdate",
        help="Sort field. Default: %(default)s",
    )
    tools_parser.add_argument(
        "--order",
        "--ord",
        dest="ord",
        choices=ORDER_OPTIONS,
        default="desc",
        help="Sort direction. Default: %(default)s",
    )
    tools_parser.add_argument(
        "--all",
        action="store_true",
        help="Fetch all result pages and merge them into one JSON document.",
    )
    tools_parser.add_argument(
        "--param",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Pass an additional raw query parameter. Repeatable.",
    )
    tools_parser.add_argument(
        "--exact",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Force exact phrase matching for a query parameter by quoting the value. Repeatable.",
    )

    for spec in TOOL_FILTERS:
        help_text = spec.description
        if spec.must_quote:
            help_text += " The CLI quotes this value automatically because the API requires it."
        tools_parser.add_argument(
            f"--{spec.option_name}",
            dest=spec.api_name,
            metavar="VALUE",
            help=help_text,
        )

    tools_parser.set_defaults(handler=handle_tools)

    tool_parser = subparsers.add_parser(
        "tool",
        parents=[common],
        help="Get a single tool by bio.tools ID",
        description="Fetch one bio.tools entry by its biotoolsID.",
        allow_abbrev=False,
    )
    tool_parser.add_argument("id", help="bio.tools tool identifier, for example 'signalp'.")
    tool_parser.add_argument(
        "--format",
        choices=DETAIL_FORMATS,
        default="json",
        help="Response format. Default: %(default)s",
    )
    tool_parser.set_defaults(handler=handle_tool)

    terms_parser = subparsers.add_parser(
        "terms",
        parents=[common],
        help="List used terms for an attribute",
        description="Return the bio.tools used-terms list for an attribute.",
        allow_abbrev=False,
    )
    terms_parser.add_argument(
        "attribute",
        help=(
            f"Used-terms attribute. One of: {', '.join(USED_TERM_ATTRIBUTES)}. "
            "Aliases accepted: function-name, function, operation, credit."
        ),
    )
    terms_parser.add_argument(
        "--format",
        choices=DETAIL_FORMATS,
        default="json",
        help="Response format. Default: %(default)s",
    )
    terms_parser.set_defaults(handler=handle_terms)

    stats_parser = subparsers.add_parser(
        "stats",
        parents=[common],
        help="Get registry statistics",
        description="Fetch registry-wide statistics from bio.tools.",
        allow_abbrev=False,
    )
    stats_parser.set_defaults(handler=handle_stats)

    domains_parser = subparsers.add_parser(
        "domains",
        parents=[common],
        help="List domains",
        description="List all domains returned by bio.tools.",
        allow_abbrev=False,
    )
    domains_parser.set_defaults(handler=handle_domains)

    domain_parser = subparsers.add_parser(
        "domain",
        parents=[common],
        help="Get information about one domain",
        description="Fetch one bio.tools domain by name.",
        allow_abbrev=False,
    )
    domain_parser.add_argument("name", help="Domain name or 'all'.")
    domain_parser.add_argument(
        "--format",
        choices=DETAIL_FORMATS,
        default="json",
        help="Response format. Default: %(default)s",
    )
    domain_parser.set_defaults(handler=handle_domain)

    filters_parser = subparsers.add_parser(
        "filters",
        help="List supported tool filters",
        description="Show the supported bio.tools tool search filters and their CLI flag names.",
        allow_abbrev=False,
    )
    filters_parser.set_defaults(handler=handle_filters)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        return args.handler(args)
    except (ApiError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        return 130


def make_client(args: argparse.Namespace) -> BioToolsClient:
    return BioToolsClient(base_url=args.base_url, timeout=args.timeout)


def parse_key_value(pairs: Sequence[str]) -> tuple[dict[str, str], set[str]]:
    params: dict[str, str] = {}
    exact_keys: set[str] = set()

    for item in pairs:
        if "=" not in item:
            raise ValueError(f"Expected KEY=VALUE, got '{item}'.")
        key, value = item.split("=", 1)
        if not key:
            raise ValueError(f"Expected KEY=VALUE, got '{item}'.")
        params[key] = value
        exact_keys.add(key)

    return params, exact_keys


def build_tool_query(args: argparse.Namespace) -> dict[str, str]:
    if args.page < 1:
        raise ValueError("--page must be at least 1.")
    if args.per_page < 1:
        raise ValueError("--per-page must be at least 1.")
    if args.sort == "score" and not args.q:
        raise ValueError(
            "--sort score requires --q because the API only exposes score sorting "
            "for query searches."
        )

    params: dict[str, Any] = {
        "page": args.page,
        "per_page": args.per_page,
        "format": args.format,
        "q": args.q,
        "sort": args.sort,
        "ord": args.ord,
    }

    for spec in TOOL_FILTERS:
        value = getattr(args, spec.api_name)
        if value is not None:
            params[spec.api_name] = value

    raw_params, _ = parse_key_value(args.param)
    exact_params, exact_keys = parse_key_value(args.exact)
    params.update(raw_params)
    params.update(exact_params)
    return normalize_tool_params(params, exact_keys=exact_keys)


def handle_tools(args: argparse.Namespace) -> int:
    client = make_client(args)
    query = build_tool_query(args)
    payload = client.list_tools(query, fetch_all=args.all)
    emit(payload, compact=args.compact)
    return 0


def handle_tool(args: argparse.Namespace) -> int:
    client = make_client(args)
    payload = client.get_tool(args.id, response_format=args.format)
    emit(payload, compact=args.compact)
    return 0


def handle_terms(args: argparse.Namespace) -> int:
    client = make_client(args)
    endpoint_attribute = resolve_used_term_endpoint(args.attribute)
    payload = client.list_used_terms(endpoint_attribute, response_format=args.format)
    emit(payload, compact=args.compact)
    return 0


def handle_stats(args: argparse.Namespace) -> int:
    client = make_client(args)
    payload = client.get_stats()
    emit(payload, compact=args.compact)
    return 0


def handle_domains(args: argparse.Namespace) -> int:
    client = make_client(args)
    payload = client.list_domains()
    emit(payload, compact=args.compact)
    return 0


def handle_domain(args: argparse.Namespace) -> int:
    client = make_client(args)
    payload = client.get_domain(args.name, response_format=args.format)
    emit(payload, compact=args.compact)
    return 0


def handle_filters(_: argparse.Namespace) -> int:
    option_width = max(len(spec.option_name) for spec in TOOL_FILTERS)
    param_width = max(len(spec.api_name) for spec in TOOL_FILTERS)

    lines = ["Supported tool search filters:"]
    for spec in TOOL_FILTERS:
        quote_note = " [auto-quoted]" if spec.must_quote else ""
        lines.append(
            
                f"  {spec.api_name:<{param_width}}"
                f"  --{spec.option_name:<{option_width}}"
                f"  {spec.description}{quote_note}"
            
        )

    lines.append("")
    lines.append(
        "Use '--exact KEY=VALUE' to force exact phrase matching for any supported parameter."
    )
    lines.append(
        "Use '--param KEY=VALUE' to pass additional raw query parameters through to the API."
    )
    print("\n".join(lines))
    return 0


def emit(payload: Any, *, compact: bool) -> None:
    if isinstance(payload, str):
        text = payload
    else:
        indent = None if compact else 2
        text = json.dumps(payload, indent=indent, ensure_ascii=False)

    if text.endswith("\n"):
        sys.stdout.write(text)
    else:
        sys.stdout.write(f"{text}\n")
