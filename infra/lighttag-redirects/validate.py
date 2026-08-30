# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Validate the LightTag CloudFront redirect function and its live endpoint.

The redirect table intentionally has one source of truth: the imported Hugo
front matter.  This module derives the 23 expected pairs from those page
bundles, extracts the JavaScript function from the deployment template, and
executes that exact function in Node for deterministic local checks.
"""

from __future__ import annotations

import argparse
import http.client
import json
import re
import socket
import ssl
import subprocess
import sys
import urllib.parse
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Final, TypeAlias, cast

import tomllib

ROOT: Final[Path] = Path(__file__).resolve().parents[2]
CONTENT_DIR: Final[Path] = ROOT / "content" / "posts" / "lighttag"
TEMPLATE_PATH: Final[Path] = Path(__file__).with_name("template.yaml")
SOURCE_HOST: Final[str] = "lighttag.io"
LIVE_HOSTS: Final[tuple[str, ...]] = ("lighttag.io", "www.lighttag.io", "guide.lighttag.io")
DESTINATION_ORIGIN: Final[str] = "https://talperry.com"
EXPECTED_PAIR_COUNT: Final[int] = 23

TomlValue: TypeAlias = str | bool | int | float | dict[str, "TomlValue"] | list["TomlValue"]
TomlTable: TypeAlias = dict[str, TomlValue]
JsonValue: TypeAlias = str | int | float | bool | None | dict[str, "JsonValue"] | list["JsonValue"]


@dataclass(frozen=True)
class RedirectPair:
    """One historical LightTag path and its canonical archive destination."""

    source: str
    destination: str


@dataclass(frozen=True)
class CloudFrontResult:
    """Small, JSON-safe subset of a CloudFront Function response."""

    status_code: int | None
    location: str | None
    request_uri: str | None


@dataclass(frozen=True)
class HttpObservation:
    """The first HTTP response, captured without following redirects."""

    status: int
    location: str | None
    final_url: str
    body: str


class _CanonicalParser(HTMLParser):
    """Read a canonical link without depending on a third-party parser."""

    def __init__(self) -> None:
        super().__init__()
        self.canonical: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "link":
            return
        values = {name.lower(): value for name, value in attrs if value is not None}
        if values.get("rel", "").lower() == "canonical":
            self.canonical = values.get("href")


def normalize_path(path: str) -> str:
    """Normalize an incoming URI path without changing its path semantics."""
    raw = path.split("?", 1)[0].split("#", 1)[0] or "/"
    if not raw.startswith("/"):
        raw = "/" + raw
    normalized = re.sub(r"/{2,}", "/", raw).lower()
    if normalized != "/":
        normalized = normalized.rstrip("/")
    return normalized or "/"


def _front_matter(text: str, source: Path) -> TomlTable:
    """Parse TOML front matter and fail with a useful source path."""
    if not text.startswith("+++"):
        raise ValueError(f"{source}: expected TOML front matter")
    end = text.find("\n+++", 3)
    if end < 0:
        raise ValueError(f"{source}: unterminated TOML front matter")
    return cast(TomlTable, tomllib.loads(text[4:end]))


def derive_expected_pairs(content_dir: Path = CONTENT_DIR) -> tuple[RedirectPair, ...]:
    """Derive and validate all source/destination pairs from imported posts."""
    pairs: list[RedirectPair] = []
    for index_path in sorted(content_dir.rglob("index.md")):
        front = _front_matter(index_path.read_text(encoding="utf-8"), index_path)
        provenance = front.get("original_publication")
        if not isinstance(provenance, dict):
            raise TypeError(f"{index_path}: missing [original_publication]")
        site = provenance.get("site")
        if not isinstance(site, str) or site.lower() != SOURCE_HOST:
            raise ValueError(f"{index_path}: source site must be LightTag.io")
        original = provenance.get("path")
        if not isinstance(original, str) or not original:
            raise ValueError(f"{index_path}: [original_publication].path must be a string")
        slug = index_path.parent.name
        destination = f"{DESTINATION_ORIGIN}/en/posts/lighttag/{slug}/"
        bundle = content_dir / slug / "index.md"
        if not bundle.is_file():
            raise ValueError(f"{index_path}: destination bundle is missing ({bundle})")
        pairs.append(RedirectPair(normalize_path(original), destination))

    if len(pairs) != EXPECTED_PAIR_COUNT:
        raise ValueError(f"expected {EXPECTED_PAIR_COUNT} imported posts, found {len(pairs)}")
    sources = [pair.source for pair in pairs]
    if len(set(sources)) != EXPECTED_PAIR_COUNT:
        raise ValueError("derived source paths are not unique")
    destinations = [pair.destination for pair in pairs]
    if len(set(destinations)) != EXPECTED_PAIR_COUNT:
        raise ValueError("derived destination paths are not unique")
    return tuple(sorted(pairs, key=lambda pair: pair.source))


def extract_function_code(template_path: Path = TEMPLATE_PATH) -> str:
    """Extract the literal CloudFront ``FunctionCode`` block from YAML.

    A dependency-free extractor keeps this validator runnable with ``uv run``
    in a clean checkout. It handles either ``FunctionCode`` or ``Code`` keys,
    as used by CloudFormation/SAM templates, and preserves JavaScript text.
    """
    lines = template_path.read_text(encoding="utf-8").splitlines()
    marker: int | None = None
    indent = 0
    for number, line in enumerate(lines):
        match = re.match(r"^(\s*)(?:FunctionCode|Code):\s*\|\s*$", line)
        if match:
            marker = number
            indent = len(match.group(1))
            break
    if marker is None:
        raise ValueError(f"{template_path}: no literal CloudFront function code block found")
    body: list[str] = []
    for line in lines[marker + 1 :]:
        if line.strip() and len(line) - len(line.lstrip()) <= indent:
            break
        body.append(line[indent + 2 :] if len(line) >= indent + 2 else "")
    code = "\n".join(body).rstrip() + "\n"
    if "function handler" not in code:
        raise ValueError(f"{template_path}: extracted code does not define handler(event)")
    return code


def extract_routes(code: str) -> dict[str, str]:
    """Extract the explicit ``routes`` allowlist from the JavaScript source."""
    block_match = re.search(r"\bvar\s+routes\s*=\s*\{(?P<body>.*?)\n\s*\};", code, re.DOTALL)
    if block_match is None:
        raise ValueError("CloudFront function has no explicit routes allowlist")
    entries = re.findall(
        r"['\"](?P<source>/[^'\"]+)['\"]\s*:\s*['\"](?P<destination>/[^'\"]+)['\"]\s*,?",
        block_match.group("body"),
    )
    routes = dict(entries)
    if len(routes) != len(entries):
        raise ValueError("CloudFront function routes allowlist contains duplicate keys")
    return routes


def validate_template_structure(template_path: Path = TEMPLATE_PATH) -> list[str]:
    """Check properties that keep unknown requests fail-closed at the edge."""
    text = template_path.read_text(encoding="utf-8")
    required = {
        "CloudFront function resource": "Type: AWS::CloudFront::Function",
        "CloudFront JS runtime": "Runtime: cloudfront-js-2.0",
        "auto-publish": "AutoPublish: true",
        "distribution resource": "Type: AWS::CloudFront::Distribution",
        "enabled distribution": "Enabled: true",
        "IPv6 distribution": "IPV6Enabled: true",
        "viewer-request association": "EventType: viewer-request",
        "one-hop viewer protocol policy": "ViewerProtocolPolicy: allow-all",
        "HTTPS-only origin": "OriginProtocolPolicy: https-only",
    }
    errors = [f"template missing {label}: {needle}" for label, needle in required.items() if needle not in text]
    aliases = {match.group(1) for match in re.finditer(r"^\s+- ([a-z0-9.-]+)$", text, re.MULTILINE)}
    for alias in ("lighttag.io", "www.lighttag.io", "guide.lighttag.io"):
        if alias not in aliases:
            errors.append(f"template distribution is missing alias {alias}")
    origin_match = re.search(r"^\s+OriginPath:\s*(\S+)", text, re.MULTILINE)
    if origin_match is None:
        errors.append("template must set a fail-closed OriginPath")
    elif origin_match.group(1) != "/__lighttag_redirect_origin_disabled__":
        errors.append("template OriginPath must use the fail-closed sentinel")
    if "return gone();" not in text:
        errors.append("template function must explicitly return gone() for unmatched requests")
    return errors


_NODE_HARNESS: Final[str] = r"""
const fs = require('fs');
const vm = require('vm');
const source = fs.readFileSync(0, 'utf8');
const input = JSON.parse(process.argv[1]);
const context = {};
vm.runInNewContext(source + '\n;globalThis.__handler = handler;', context);
const output = context.__handler(input);
process.stdout.write(JSON.stringify(output));
"""


def execute_function(
    code: str,
    uri: str,
    querystring: str = "",
    host: str = SOURCE_HOST,
    method: str = "GET",
) -> CloudFrontResult:
    """Execute extracted CloudFront JavaScript in a local Node VM."""
    query_event: dict[str, dict[str, str]] = {}
    for item in querystring.split("&") if querystring else []:
        key, separator, value = item.partition("=")
        if key:
            query_event[key] = {"value": value if separator else ""}
    event = {
        "request": {
            "uri": uri,
            "method": method,
            "querystring": query_event,
            "headers": {"host": {"value": host}},
        }
    }
    try:
        completed = subprocess.run(
            ["node", "-e", _NODE_HARNESS, json.dumps(event)],
            input=code,
            text=True,
            capture_output=True,
            check=True,
            timeout=5,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("Node.js is required to execute the CloudFront function") from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"CloudFront function failed: {exc.stderr.strip()}") from exc
    result = json.loads(completed.stdout)
    if not isinstance(result, dict):
        raise TypeError("CloudFront function returned a non-mapping result")
    headers = result.get("headers")
    location: str | None = None
    if isinstance(headers, dict):
        header = headers.get("location")
        if isinstance(header, dict) and isinstance(header.get("value"), str):
            location = header["value"]
    status = result.get("statusCode")
    return CloudFrontResult(
        status_code=status if isinstance(status, int) else None,
        location=location,
        request_uri=result.get("uri") if isinstance(result.get("uri"), str) else None,
    )


def validate_local(template_path: Path = TEMPLATE_PATH) -> list[str]:
    """Run all offline mapping, normalization, and pass-through assertions."""
    pairs = derive_expected_pairs()
    code = extract_function_code(template_path)
    errors: list[str] = []
    errors.extend(validate_template_structure(template_path))
    routes = extract_routes(code)
    expected_routes = {
        pair.source: pair.destination.removeprefix(DESTINATION_ORIGIN) for pair in pairs
    }
    if routes != expected_routes:
        errors.append(f"template routes differ from front matter (expected {len(expected_routes)}, got {len(routes)})")
    by_source = {pair.source: pair for pair in pairs}
    for pair in pairs:
        variants = set(_path_variants(pair.source))
        for method in ("GET", "HEAD"):
            for variant in variants:
                result = execute_function(code, variant, method=method)
                if result.status_code != 301 or result.location != pair.destination:
                    errors.append(f"{method} {variant}: expected 301 Location {pair.destination}, got {result}")

        # The corrected spelling is accepted as a compatibility alias, but is
        # intentionally not a 24th historical route in the allowlist.
        if pair.source.endswith("-imporvement"):
            corrected = pair.source.replace("-imporvement", "-improvement")
            for method in ("GET", "HEAD"):
                result = execute_function(code, corrected, method=method)
                if result.status_code != 301 or result.location != pair.destination:
                    errors.append(f"{method} {corrected}: corrected spelling did not redirect")

        query = "utm_source=archive&x=1"
        for method in ("GET", "HEAD"):
            result = execute_function(code, pair.source, query, method=method)
            expected_location = pair.destination
            if result.status_code != 301 or result.location != expected_location:
                errors.append(f"{method} {pair.source}: query string must be dropped from canonical Location")

    # Root and guide are deliberately explicit: these are common migration URLs.
    for root_path in ("/", "/index.html", "/index.html/"):
        for method in ("GET", "HEAD"):
            root = execute_function(code, root_path, "utm_source=archive&x=1", method=method)
            if root.status_code != 301 or root.location != f"{DESTINATION_ORIGIN}/":
                errors.append(f"{method} {root_path}: expected archive root redirect, got {root}")
    for guide_uri in ("/", "/guide", "/guide/", "/guide/index.html"):
        for method in ("GET", "HEAD"):
            guide = execute_function(code, guide_uri, host="guide.lighttag.io", method=method)
            if guide.status_code != 410 or guide.location is not None:
                errors.append(f"{method} guide.lighttag.io{guide_uri}: expected 410 Gone, got {guide}")
    for method in ("GET", "HEAD"):
        main_guide = execute_function(code, "/guide/", method=method)
        if main_guide.status_code != 410 or main_guide.location is not None:
            errors.append(f"{method} /guide/ must return 410 Gone")

    for method in ("GET", "HEAD"):
        unknown = execute_function(code, "/blog/not-an-imported-post/", method=method)
        if unknown.status_code != 410 or unknown.location is not None:
            errors.append(f"{method} unknown path must return 410 Gone, got {unknown}")
    if by_source and len(by_source) != EXPECTED_PAIR_COUNT:
        errors.append("expected mapping count changed during local validation")
    return errors


def _path_variants(path: str) -> tuple[str, ...]:
    """Return slash, case, and legacy index variants for a normalized path."""
    variants = [path, path + "/", path.upper(), path.upper() + "//"]
    separator = path.find("/", 1)
    if separator > 0:
        variants.append(path[:separator] + "//" + path[separator + 1 :])
    variants.extend((path + "/index.html", path + "/index.html/"))
    if path.endswith("-imporvement"):
        corrected = path.replace("-imporvement", "-improvement")
        variants.extend((corrected, corrected + "/", corrected + "/index.html"))
    return tuple(dict.fromkeys(variants))


def _request_direct(
    logical_host: str,
    scheme: str,
    path: str,
    query: str,
    timeout_s: float,
    method: str = "GET",
    connect_host: str | None = None,
    connect_address: tuple[socket.AddressFamily, str] | None = None,
) -> HttpObservation:
    """Request a URL while separating logical Host/SNI from connect target."""
    port = 443 if scheme == "https" else 80
    target = connect_host or logical_host
    request_target = path + (f"?{query}" if query else "")
    full_url = f"{scheme}://{logical_host}{request_target}"
    if connect_address is None:
        raw: socket.socket = socket.create_connection((target, port), timeout=timeout_s)
    else:
        family, address = connect_address
        raw = socket.socket(family, socket.SOCK_STREAM)
        raw.settimeout(timeout_s)
        raw.connect((address, port))
    try:
        secure: socket.socket | ssl.SSLSocket = raw
        if scheme == "https":
            context = ssl.create_default_context()
            secure = context.wrap_socket(raw, server_hostname=logical_host)
        connection = http.client.HTTPConnection(logical_host)
        connection.sock = secure
        try:
            connection.request(method, request_target, headers={"Host": logical_host, "Connection": "close"})
            response = connection.getresponse()
            body = "" if method == "HEAD" else response.read().decode("utf-8", errors="replace")
            return HttpObservation(response.status, response.headers.get("Location"), full_url, body)
        finally:
            connection.close()
    finally:
        raw.close()


def _resolve_addresses(
    host: str, family: socket.AddressFamily
) -> list[tuple[socket.AddressFamily, tuple[str, int]]]:
    """Resolve unique TCP addresses for one IP family."""
    addresses: list[tuple[socket.AddressFamily, tuple[str, int]]] = []
    seen: set[str] = set()
    for item in socket.getaddrinfo(host, 443, family, socket.SOCK_STREAM):
        resolved_family, _, _, _, sockaddr = item
        address = str(sockaddr[0])
        if address not in seen:
            seen.add(address)
            addresses.append((resolved_family, (address, 443)))
    return addresses


def validate_live(
    host: str | None = None,
    timeout_s: float = 8.0,
    connect_host: str | None = None,
) -> list[str]:
    """Validate all public hosts, methods, families, and canonical targets.

    ``host`` selects a logical Host/SNI name for an optional focused run.
    ``connect_host`` changes only DNS and TCP connection routing (for example
    to a CloudFront distribution name); HTTP Host and TLS SNI remain logical.
    HTTP and HTTPS both assert the direct viewer-request result because a
    generated response stops further CloudFront processing.
    """
    pairs = derive_expected_pairs()
    hosts = (host,) if host else LIVE_HOSTS
    errors: list[str] = []
    query = "utm_source=archive&x=1"
    representative = pairs[0]

    for current_host in hosts:
        target = connect_host or current_host
        resolved: dict[socket.AddressFamily, list[tuple[socket.AddressFamily, tuple[str, int]]]] = {}
        for family, label in ((socket.AF_INET, "IPv4"), (socket.AF_INET6, "IPv6")):
            try:
                resolved[family] = _resolve_addresses(target, family)
                if not resolved[family]:
                    errors.append(f"{target}: no {label} DNS record")
            except socket.gaierror as exc:
                errors.append(f"{target}: {label} DNS lookup failed: {exc}")

        context = ssl.create_default_context()
        for family, addresses in resolved.items():
            for _, sockaddr in addresses:
                try:
                    with socket.socket(family, socket.SOCK_STREAM) as raw:
                        raw.settimeout(timeout_s)
                        raw.connect(sockaddr)
                        with context.wrap_socket(raw, server_hostname=current_host):
                            pass
                except (OSError, ssl.SSLError) as exc:
                    errors.append(f"{current_host}: TLS failed for {sockaddr[0]}: {exc}")

        guide_host = current_host == "guide.lighttag.io"
        probes: list[tuple[str, str | None]] = [
            ("/", None if guide_host else f"{DESTINATION_ORIGIN}/"),
            ("/index.html", None if guide_host else f"{DESTINATION_ORIGIN}/"),
            ("/guide", None),
            ("/guide/", None),
            ("/__lighttag-redirect-unknown__", None),
        ]
        for pair in pairs:
            expected = None if guide_host else pair.destination
            probes.extend((path, expected) for path in _path_variants(pair.source))

        for path, expected_location in probes:
            for scheme in ("http", "https"):
                url = f"{scheme}://{current_host}{path}?{query}"
                for method in ("GET", "HEAD"):
                    try:
                        result = _request_direct(
                            current_host,
                            scheme,
                            path,
                            query,
                            timeout_s,
                            method=method,
                            connect_host=connect_host,
                        )
                    except OSError as exc:
                        errors.append(f"{method} {url}: request failed: {exc}")
                        continue
                    if expected_location is None:
                        if result.status != 410 or result.location is not None:
                            errors.append(f"{method} {url}: expected exact 410 Gone, got {result.status} {result.location!r}")
                    elif result.status != 301 or result.location != expected_location:
                        errors.append(
                            f"{method} {url}: expected exact 301 Location {expected_location!r}, "
                            f"got {result.status} {result.location!r}"
                        )

        # One GET and HEAD probe per resolved family verifies application
        # behavior on actual addresses without multiplying the full matrix.
        if not guide_host:
            for family, addresses in resolved.items():
                if not addresses:
                    continue
                _, (address, _) = addresses[0]
                for method in ("GET", "HEAD"):
                    try:
                        result = _request_direct(
                            current_host,
                            "https",
                            representative.source,
                            query,
                            timeout_s,
                            method=method,
                            connect_address=(family, address),
                        )
                    except OSError as exc:
                        errors.append(f"{method} {current_host} [{address}]: pinned request failed: {exc}")
                        continue
                    if result.status != 301 or result.location != representative.destination:
                        errors.append(
                            f"{method} {current_host} [{address}]: expected exact 301 Location "
                            f"{representative.destination!r}, got {result.status} {result.location!r}"
                        )

    if any(current_host != "guide.lighttag.io" for current_host in hosts):
        for pair in pairs:
            parsed = urllib.parse.urlsplit(pair.destination)
            try:
                destination = _request_direct(
                    parsed.hostname or "",
                    parsed.scheme,
                    parsed.path or "/",
                    parsed.query,
                    timeout_s,
                )
            except OSError as exc:
                errors.append(f"{pair.destination}: destination request failed: {exc}")
                continue
            if destination.status != 200 or destination.final_url != pair.destination:
                errors.append(
                    f"{pair.destination}: expected one-hop 200 destination, "
                    f"got {destination.status} at {destination.final_url!r}"
                )
            parser = _CanonicalParser()
            parser.feed(destination.body)
            if parser.canonical != pair.destination:
                errors.append(
                    f"{pair.destination}: canonical metadata is {parser.canonical!r}, expected {pair.destination!r}"
                )
    return errors


def main(argv: list[str] | None = None) -> int:
    """CLI entry point; local checks are the default and never use network."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="also check DNS, TLS, and deployed redirects")
    parser.add_argument("--host", default=None, help="optional source hostname override for --live")
    parser.add_argument("--connect-host", default=None, help="optional DNS/TCP target; preserves logical Host/SNI")
    args = parser.parse_args(argv)
    errors = validate_local()
    if args.live:
        errors.extend(validate_live(args.host, connect_host=args.connect_host))
    if errors:
        print("LightTag redirect validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("LightTag redirect validation passed" + (" (live)" if args.live else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
