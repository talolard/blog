# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""Offline tests for the guarded IndexNow integration."""

from __future__ import annotations

import json
import tempfile
import unittest
from collections.abc import Mapping
from pathlib import Path
from unittest.mock import patch

import submit_indexnow


class IndexNowTests(unittest.TestCase):
    def test_recursively_collects_all_languages_and_deduplicates(self) -> None:
        documents = {
            "https://talperry.com/sitemap.xml": b"""
                <sitemapindex xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'>
                  <sitemap><loc>https://talperry.com/en/sitemap.xml</loc></sitemap>
                  <sitemap><loc>https://talperry.com/de/sitemap.xml</loc></sitemap>
                  <sitemap><loc>https://talperry.com/he/sitemap.xml</loc></sitemap>
                </sitemapindex>
            """,
            "https://talperry.com/en/sitemap.xml": b"""
                <urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'>
                  <url><loc>https://talperry.com/en/</loc></url>
                  <url><loc>https://talperry.com/about/</loc></url>
                </urlset>
            """,
            "https://talperry.com/de/sitemap.xml": b"""
                <urlset><url><loc>https://talperry.com/de/</loc></url>
                  <url><loc>https://talperry.com/about/</loc></url></urlset>
            """,
            "https://talperry.com/he/sitemap.xml": b"<urlset><url><loc>https://talperry.com/he/</loc></url></urlset>",
        }

        def fake_request(
            url: str,
            method: str,
            body: bytes | None,
            headers: Mapping[str, str] | None,
        ) -> submit_indexnow.HttpResponse:
            del method, body, headers
            return submit_indexnow.HttpResponse(200, documents[url])

        self.assertEqual(
            submit_indexnow.collect_sitemap_urls(requester=fake_request),
            [
                "https://talperry.com/en/",
                "https://talperry.com/about/",
                "https://talperry.com/de/",
                "https://talperry.com/he/",
            ],
        )

    def test_rejects_foreign_and_non_https_sitemap_entries(self) -> None:
        for loc in ("http://talperry.com/en/", "https://example.com/en/"):
            xml = f"<urlset><url><loc>{loc}</loc></url></urlset>".encode()

            def fake_request(
                url: str,
                method: str,
                body: bytes | None,
                headers: Mapping[str, str] | None,
                document: bytes = xml,
            ) -> submit_indexnow.HttpResponse:
                del url, method, body, headers
                return submit_indexnow.HttpResponse(200, document)

            with self.assertRaises(submit_indexnow.IndexNowError):
                submit_indexnow.collect_sitemap_urls(requester=fake_request)

    def test_batches_respect_url_count_limit(self) -> None:
        urls = [f"https://talperry.com/en/posts/{index}/" for index in range(10_001)]
        batches = submit_indexnow.build_batches(urls, "a" * 32, submit_indexnow.DEFAULT_KEY_LOCATION)
        self.assertEqual([len(batch) for batch in batches], [10_000, 1])

    def test_oversized_first_url_fails_closed(self) -> None:
        huge_url = "https://talperry.com/" + ("x" * submit_indexnow.CONSERVATIVE_MAX_BATCH_BYTES)
        with self.assertRaisesRegex(submit_indexnow.IndexNowError, "local safety ceiling"):
            submit_indexnow.build_batches([huge_url], "a" * 32, submit_indexnow.DEFAULT_KEY_LOCATION)

    def test_key_endpoint_is_checked_before_global_posts(self) -> None:
        calls: list[tuple[str, str]] = []
        key = "a" * 32

        def fake_request(
            url: str,
            method: str,
            body: bytes | None,
            headers: Mapping[str, str] | None,
        ) -> submit_indexnow.HttpResponse:
            del headers
            calls.append((url, method))
            if method == "GET":
                return submit_indexnow.HttpResponse(
                    200,
                    (key + "\n").encode(),
                    final_url=submit_indexnow.DEFAULT_KEY_LOCATION,
                )
            if body is None:
                raise AssertionError("POST request must have a JSON body")
            payload = json.loads(body.decode())
            self.assertEqual(payload["host"], "talperry.com")
            self.assertEqual(payload["key"], key)
            return submit_indexnow.HttpResponse(200, b"{}", final_url=submit_indexnow.INDEXNOW_ENDPOINT)

        submit_indexnow.validate_key_endpoint(key, submit_indexnow.DEFAULT_KEY_LOCATION, requester=fake_request)
        statuses = submit_indexnow.submit_batches(
            [["https://talperry.com/en/", "https://talperry.com/de/"]],
            key,
            submit_indexnow.DEFAULT_KEY_LOCATION,
            requester=fake_request,
        )
        self.assertEqual([result.status for result in statuses], [200])
        self.assertEqual(statuses[0].batch_number, 1)
        self.assertTrue(statuses[0].submitted_at.endswith("Z"))
        self.assertIn("sha256=", statuses[0].body_evidence)
        self.assertEqual(
            calls,
            [
                (submit_indexnow.DEFAULT_KEY_LOCATION, "GET"),
                (submit_indexnow.INDEXNOW_ENDPOINT, "POST"),
            ],
        )

    def test_dry_run_does_not_request_key_endpoint_or_post(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            key_path = Path(directory) / "key.txt"
            key_path.write_text("b" * 32, encoding="ascii")

            def fake_collect(
                sitemap_url: str = submit_indexnow.DEFAULT_SITEMAP_URL,
                *,
                requester: submit_indexnow.Requester | None = None,
            ) -> list[str]:
                del sitemap_url, requester
                return ["https://talperry.com/en/"]

            with patch.object(submit_indexnow, "collect_sitemap_urls", fake_collect):
                self.assertEqual(submit_indexnow.main(["--dry-run", "--key-file", str(key_path)]), 0)

    def test_submission_distinguishes_200_and_202(self) -> None:
        responses = [
            submit_indexnow.HttpResponse(200, b"done", final_url=submit_indexnow.INDEXNOW_ENDPOINT),
            submit_indexnow.HttpResponse(202, b"pending", final_url=submit_indexnow.INDEXNOW_ENDPOINT),
        ]

        def fake_request(
            url: str,
            method: str,
            body: bytes | None,
            headers: Mapping[str, str] | None,
        ) -> submit_indexnow.HttpResponse:
            del url, method, body, headers
            return responses.pop(0)

        results = submit_indexnow.submit_batches(
            [["https://talperry.com/en/"], ["https://talperry.com/de/"]],
            "a" * 32,
            submit_indexnow.DEFAULT_KEY_LOCATION,
            requester=fake_request,
        )
        self.assertEqual([result.status for result in results], [200, 202])
        self.assertEqual(submit_indexnow.submission_state(results[0].status), "success")
        self.assertEqual(submit_indexnow.submission_state(results[1].status), "accepted/pending")

    def test_204_is_not_success(self) -> None:
        def fake_request(
            url: str,
            method: str,
            body: bytes | None,
            headers: Mapping[str, str] | None,
        ) -> submit_indexnow.HttpResponse:
            del url, method, body, headers
            return submit_indexnow.HttpResponse(204, b"")

        with self.assertRaisesRegex(submit_indexnow.IndexNowError, "HTTP 204.*evidence=sha256="):
            submit_indexnow.submit_batches(
                [["https://talperry.com/en/"]],
                "a" * 32,
                submit_indexnow.DEFAULT_KEY_LOCATION,
                requester=fake_request,
            )

    def test_429_retains_retry_after_in_error(self) -> None:
        def fake_request(
            url: str,
            method: str,
            body: bytes | None,
            headers: Mapping[str, str] | None,
        ) -> submit_indexnow.HttpResponse:
            del url, method, body, headers
            return submit_indexnow.HttpResponse(429, b"slow down", {"retry-after": "60"})

        with self.assertRaisesRegex(submit_indexnow.IndexNowError, "HTTP 429.*evidence=sha256=.*retry-after=60"):
            submit_indexnow.submit_batches(
                [["https://talperry.com/en/"]],
                "a" * 32,
                submit_indexnow.DEFAULT_KEY_LOCATION,
                requester=fake_request,
            )

    def test_key_accepts_protocol_charset_and_preserves_case(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "key.txt"
            value = "AbC-1234" + ("Z" * 120)
            path.write_text(value, encoding="ascii")
            self.assertEqual(submit_indexnow.load_public_key(path), value)

    def test_key_rejects_non_protocol_characters(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "key.txt"
            for value in ("short", "abcd_1234", "abcd 1234"):
                path.write_text(value, encoding="ascii")
                with self.assertRaises(submit_indexnow.IndexNowError):
                    submit_indexnow.load_public_key(path)

    def test_key_endpoint_comparison_is_case_sensitive_and_redirect_safe(self) -> None:
        key = "AbCd-1234"
        endpoint = submit_indexnow.DEFAULT_KEY_LOCATION

        def mismatched_case(
            url: str,
            method: str,
            body: bytes | None,
            headers: Mapping[str, str] | None,
        ) -> submit_indexnow.HttpResponse:
            del url, method, body, headers
            return submit_indexnow.HttpResponse(200, b"abcd-1234", final_url=endpoint)

        with self.assertRaisesRegex(submit_indexnow.IndexNowError, "does not serve"):
            submit_indexnow.validate_key_endpoint(key, endpoint, requester=mismatched_case)

        def redirected(
            url: str,
            method: str,
            body: bytes | None,
            headers: Mapping[str, str] | None,
        ) -> submit_indexnow.HttpResponse:
            del url, method, body, headers
            return submit_indexnow.HttpResponse(200, key.encode(), final_url="https://talperry.com/other-key.txt")

        with self.assertRaisesRegex(submit_indexnow.IndexNowError, "redirected"):
            submit_indexnow.validate_key_endpoint(key, endpoint, requester=redirected)

    def test_empty_sitemap_refuses_before_submission(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            key_path = Path(directory) / "key.txt"
            key_path.write_text("a" * 32, encoding="ascii")

            def fake_collect(
                sitemap_url: str = submit_indexnow.DEFAULT_SITEMAP_URL,
                *,
                requester: submit_indexnow.Requester | None = None,
            ) -> list[str]:
                del sitemap_url, requester
                return []

            with patch.object(submit_indexnow, "collect_sitemap_urls", fake_collect):
                self.assertEqual(submit_indexnow.main(["--submit", "--confirm", "SUBMIT INDEXNOW", "--key-file", str(key_path)]), 1)

    def test_redirected_post_is_rejected(self) -> None:
        def fake_request(
            url: str,
            method: str,
            body: bytes | None,
            headers: Mapping[str, str] | None,
        ) -> submit_indexnow.HttpResponse:
            del url, method, body, headers
            return submit_indexnow.HttpResponse(200, b"landing", final_url="https://example.com/")

        with self.assertRaisesRegex(submit_indexnow.SubmissionError, "POST redirected"):
            submit_indexnow.submit_batches(
                [["https://talperry.com/en/"]],
                "a" * 32,
                submit_indexnow.DEFAULT_KEY_LOCATION,
                requester=fake_request,
            )

    def test_confirmation_refusal_happens_before_sitemap(self) -> None:
        self.assertEqual(submit_indexnow.main(["--submit", "--confirm", "WRONG"]), 2)


if __name__ == "__main__":
    unittest.main()
