# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""Collect the production sitemap and submit its canonical URLs to IndexNow.

The default mode is a read-only dry run. Submission is intentionally guarded
by both ``--submit`` and an exact confirmation phrase because this program
contacts a third-party indexing service.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from http.client import HTTPMessage
from pathlib import Path
from typing import IO
from urllib.parse import urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SITEMAP_URL = "https://talperry.com/sitemap.xml"
DEFAULT_KEY_FILE = ROOT / "static" / "indexnow-key.txt"
DEFAULT_KEY_LOCATION = "https://talperry.com/indexnow-key.txt"
INDEXNOW_ENDPOINT = "https://api.indexnow.org/indexnow"
INDEXNOW_HOST = "talperry.com"
MAX_URLS_PER_BATCH = 10_000
# This is a conservative local request-size ceiling, not an IndexNow protocol
# limit. The protocol limit enforced below is MAX_URLS_PER_BATCH.
CONSERVATIVE_MAX_BATCH_BYTES = 1_000_000
CONFIRMATION = "SUBMIT INDEXNOW"
KEY_PATTERN = re.compile(r"\A[A-Za-z0-9-]{8,128}\Z")


class IndexNowError(ValueError):
    """A local sitemap, key, or protocol invariant is invalid."""


@dataclass(frozen=True)
class HttpResponse:
    """The small portion of an HTTP response needed by this integration."""

    status: int
    body: bytes
    headers: Mapping[str, str] = field(default_factory=dict)
    final_url: str = ""


@dataclass(frozen=True)
class SubmissionResult:
    """Auditable, non-sensitive evidence for one IndexNow request."""

    batch_number: int
    url_count: int
    submitted_at: str
    status: int
    body_evidence: str
    retry_after: str | None


class SubmissionError(IndexNowError):
    """A failed batch together with successful prior-batch evidence."""

    def __init__(self, message: str, completed: Sequence[SubmissionResult]) -> None:
        super().__init__(message)
        self.completed = tuple(completed)


Requester = Callable[[str, str, bytes | None, Mapping[str, str] | None], HttpResponse]


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Make sitemap and IndexNow requests fail closed instead of following 3xx."""

    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: IO[bytes],
        code: int,
        msg: str,
        headers: HTTPMessage,
        newurl: str,
    ) -> urllib.request.Request | None:
        del req, fp, code, msg, headers, newurl
        return None


def request_url(
    url: str,
    method: str = "GET",
    body: bytes | None = None,
    headers: Mapping[str, str] | None = None,
    *,
    timeout: float = 30.0,
) -> HttpResponse:
    """Perform one HTTP request with a bounded timeout."""

    request = urllib.request.Request(url, data=body, headers=dict(headers or {}), method=method)
    try:
        opener = urllib.request.build_opener(NoRedirectHandler())
        with opener.open(request, timeout=timeout) as response:
            headers = {str(name): str(value) for name, value in response.headers.items()}
            return HttpResponse(
                status=response.status,
                body=response.read(),
                headers=headers,
                final_url=response.geturl(),
            )
    except urllib.error.HTTPError as error:
        headers = {str(name): str(value) for name, value in error.headers.items()}
        return HttpResponse(status=error.code, body=error.read(), headers=headers, final_url=error.geturl())
    except urllib.error.URLError as error:
        raise IndexNowError(f"request failed for {url}: {error.reason}") from error


def local_name(tag: str) -> str:
    """Return an XML tag's local name, independent of its namespace."""

    return tag.rsplit("}", 1)[-1]


def validate_public_url(value: str, *, label: str) -> str:
    """Validate and normalize a canonical URL belonging to Tal Perry."""

    try:
        parsed = urlsplit(value.strip())
        hostname = parsed.hostname
        port = parsed.port
    except ValueError as error:
        raise IndexNowError(f"{label} is not a valid URL: {value!r}") from error
    if parsed.scheme.lower() != "https":
        raise IndexNowError(f"{label} must use HTTPS: {value!r}")
    if hostname is None or hostname.lower() != INDEXNOW_HOST:
        raise IndexNowError(f"{label} must use host {INDEXNOW_HOST}: {value!r}")
    if port is not None or parsed.username is not None or parsed.password is not None:
        raise IndexNowError(f"{label} must not include credentials or a port: {value!r}")
    if parsed.query or parsed.fragment:
        raise IndexNowError(f"{label} must not include a query or fragment: {value!r}")
    return urlunsplit(("https", INDEXNOW_HOST, parsed.path or "/", "", ""))


def sitemap_children(root: ET.Element, name: str) -> list[str]:
    """Extract non-empty ``loc`` values from children of a sitemap node."""

    values: list[str] = []
    for element in root.iter():
        if local_name(element.tag) != name:
            continue
        for child in element:
            if local_name(child.tag) == "loc" and child.text and child.text.strip():
                values.append(child.text.strip())
    return values


def collect_sitemap_urls(
    sitemap_url: str = DEFAULT_SITEMAP_URL,
    *,
    requester: Requester | None = None,
) -> list[str]:
    """Recursively collect and deduplicate every valid URL in a sitemap tree."""

    request = requester or request_url
    root_url = validate_public_url(sitemap_url, label="sitemap URL")
    pending = [root_url]
    visited: set[str] = set()
    urls: list[str] = []
    seen_urls: set[str] = set()

    while pending:
        current = pending.pop(0)
        if current in visited:
            continue
        visited.add(current)
        response = request(current, "GET", None, {"Accept": "application/xml, text/xml"})
        if response.status < 200 or response.status >= 300:
            raise IndexNowError(f"sitemap request returned HTTP {response.status}: {current}")
        try:
            root = ET.fromstring(response.body)
        except ET.ParseError as error:
            raise IndexNowError(f"invalid XML in sitemap {current}: {error}") from error

        kind = local_name(root.tag)
        if kind == "sitemapindex":
            for child_url in sitemap_children(root, "sitemap"):
                pending.append(validate_public_url(child_url, label="sitemap child URL"))
        elif kind == "urlset":
            for page_url in sitemap_children(root, "url"):
                normalized = validate_public_url(page_url, label="sitemap page URL")
                if normalized not in seen_urls:
                    seen_urls.add(normalized)
                    urls.append(normalized)
        else:
            raise IndexNowError(f"unsupported sitemap root <{kind}> in {current}")

    return urls


def load_public_key(path: Path = DEFAULT_KEY_FILE) -> str:
    """Read and validate the 8-128 ASCII letter/digit/hyphen public key."""

    try:
        key = path.read_text(encoding="utf-8").strip()
    except OSError as error:
        raise IndexNowError(f"cannot read IndexNow public key {path}: {error}") from error
    if not KEY_PATTERN.fullmatch(key):
        raise IndexNowError("IndexNow public key must contain 8-128 ASCII letters, digits, or hyphens")
    return key


def payload_bytes(key: str, key_location: str, urls: Sequence[str]) -> bytes:
    """Encode one compact IndexNow JSON request body."""

    payload: dict[str, str | list[str]] = {
        "host": INDEXNOW_HOST,
        "key": key,
        "keyLocation": key_location,
        "urlList": list(urls),
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def build_batches(urls: Sequence[str], key: str, key_location: str) -> list[list[str]]:
    """Split URLs by protocol count and a conservative local size ceiling."""

    batches: list[list[str]] = []
    current: list[str] = []
    for url in urls:
        candidate = current + [url]
        too_large = len(payload_bytes(key, key_location, candidate)) > CONSERVATIVE_MAX_BATCH_BYTES
        if current and (
            len(candidate) > MAX_URLS_PER_BATCH
            or too_large
        ):
            batches.append(current)
            current = [url]
            if len(payload_bytes(key, key_location, current)) > CONSERVATIVE_MAX_BATCH_BYTES:
                raise IndexNowError(
                    f"single URL exceeds the {CONSERVATIVE_MAX_BATCH_BYTES}-byte local safety ceiling: {url}"
                )
        elif not current and too_large:
            raise IndexNowError(
                f"single URL exceeds the {CONSERVATIVE_MAX_BATCH_BYTES}-byte local safety ceiling: {url}"
            )
        else:
            current = candidate
    if current:
        batches.append(current)
    return batches


def validate_key_endpoint(
    key: str,
    key_location: str,
    *,
    requester: Requester,
) -> None:
    """Ensure the deployed key endpoint is HTTPS and serves this exact key."""

    endpoint = validate_public_url(key_location, label="key endpoint")
    response = requester(endpoint, "GET", None, {"Accept": "text/plain"})
    if response.status != 200:
        raise IndexNowError(
            f"key endpoint returned HTTP {response.status}: {endpoint}; evidence={body_evidence(response.body)}"
        )
    if response.final_url != endpoint:
        raise IndexNowError(
            f"key endpoint redirected; expected final URL {endpoint}, got {response.final_url or '<unknown>'}"
        )
    try:
        served_key = response.body.decode("ascii").strip()
    except UnicodeDecodeError as error:
        raise IndexNowError(f"key endpoint is not ASCII text: {endpoint}") from error
    if served_key != key:
        raise IndexNowError(f"key endpoint does not serve the local public key: {endpoint}")


def body_evidence(body: bytes) -> str:
    """Return bounded evidence without retaining or printing response content."""

    return f"sha256={sha256(body).hexdigest()};bytes={len(body)}"


def response_header(headers: Mapping[str, str], name: str) -> str | None:
    """Read a response header case-insensitively."""

    wanted = name.lower()
    for header_name, value in headers.items():
        if header_name.lower() == wanted:
            return value
    return None


def utc_timestamp() -> str:
    """Return an unambiguous UTC timestamp for retained submission evidence."""

    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def submission_state(status: int) -> str:
    """Describe the two successful protocol outcomes distinctly."""

    if status == 200:
        return "success"
    if status == 202:
        return "accepted/pending"
    raise IndexNowError(f"unsupported successful IndexNow status: {status}")


def submit_batches(
    batches: Sequence[Sequence[str]],
    key: str,
    key_location: str,
    *,
    requester: Requester,
) -> list[SubmissionResult]:
    """POST each bounded batch to the single global IndexNow endpoint."""

    results: list[SubmissionResult] = []
    for batch_number, batch in enumerate(batches, start=1):
        response = requester(
            INDEXNOW_ENDPOINT,
            "POST",
            payload_bytes(key, key_location, batch),
            {"Content-Type": "application/json; charset=utf-8", "Accept": "application/json"},
        )
        evidence = body_evidence(response.body)
        if response.status not in (200, 202):
            retry_after = response_header(response.headers, "Retry-After")
            retry_detail = f"; retry-after={retry_after}" if retry_after is not None else ""
            raise SubmissionError(
                f"IndexNow returned HTTP {response.status} for batch {batch_number} "
                f"({len(batch)} URLs) at {utc_timestamp()}; evidence={evidence}{retry_detail}",
                results,
            )
        if response.final_url != INDEXNOW_ENDPOINT:
            raise SubmissionError(
                f"IndexNow POST redirected; expected final URL {INDEXNOW_ENDPOINT}, "
                f"got {response.final_url or '<unknown>'}; evidence={evidence}",
                results,
            )
        results.append(
            SubmissionResult(
                batch_number=batch_number,
                url_count=len(batch),
                submitted_at=utc_timestamp(),
                status=response.status,
                body_evidence=evidence,
                retry_after=response_header(response.headers, "Retry-After"),
            )
        )
    return results


def parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""

    result = argparse.ArgumentParser(description=__doc__)
    mode = result.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="collect and report URLs without any submission")
    mode.add_argument("--submit", action="store_true", help="submit URL batches to IndexNow")
    result.add_argument("--confirm", help=f"required with --submit; must equal {CONFIRMATION!r}")
    result.add_argument("--sitemap-url", default=DEFAULT_SITEMAP_URL)
    result.add_argument("--key-file", type=Path, default=DEFAULT_KEY_FILE)
    result.add_argument("--key-location", default=DEFAULT_KEY_LOCATION)
    return result


def format_submission_result(result: SubmissionResult, batch_count: int) -> str:
    """Format one retained batch result without exposing response content."""

    retry_detail = f"; retry-after={result.retry_after}" if result.retry_after is not None else ""
    return (
        f"batch {result.batch_number}/{batch_count}: status={result.status} "
        f"({submission_state(result.status)}) at {result.submitted_at}; "
        f"evidence={result.body_evidence}{retry_detail}"
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Run a dry-run report or an explicitly confirmed submission."""

    args = parser().parse_args(argv)
    submit = bool(args.submit)
    if submit and args.confirm != CONFIRMATION:
        print(f"Refusing submission: pass --confirm {CONFIRMATION!r}", file=sys.stderr)
        return 2
    if not submit and args.confirm:
        print("--confirm is only valid with --submit", file=sys.stderr)
        return 2

    try:
        key = load_public_key(args.key_file)
        key_location = validate_public_url(args.key_location, label="key endpoint")
        urls = collect_sitemap_urls(args.sitemap_url)
        if not urls:
            raise IndexNowError("production sitemap contained no canonical URLs; refusing submission")
        batches = build_batches(urls, key, key_location)
        print(f"Collected {len(urls)} canonical URLs in {len(batches)} IndexNow batch(es)")
        if not submit:
            print("Dry run: no key endpoint or IndexNow submission request was made")
            return 0
        validate_key_endpoint(key, key_location, requester=request_url)
        results = submit_batches(batches, key, key_location, requester=request_url)
        for result in results:
            print(format_submission_result(result, len(batches)))
    except SubmissionError as error:
        for result in error.completed:
            print(format_submission_result(result, len(batches)))
        print(f"IndexNow submission failed: {error}", file=sys.stderr)
        return 1
    except IndexNowError as error:
        print(f"IndexNow submission failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
