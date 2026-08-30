"""Regression coverage for the restored LightTag article archive."""

from __future__ import annotations

import subprocess
from datetime import date
from pathlib import Path

import pytest
from PIL import Image
from playwright.sync_api import Page


POSTS = (
    ("active-learning-manager", "2020-05-10", "ALMa: Active Learning (Data) Manager"),
    ("active-learning-optimization-is-not-improvement", "2018-06-03", "Active Learning: Optimization Is Not Improvement"),
    ("psql-range-aggregation-for-nlp", "2019-10-18", "Postgres Range Aggregation for NLP and Everything Else"),
    ("indexeddb-for-nlp", "2019-07-08", "The Joy of IndexedDB for NLP"),
    ("character-level-nlp", "2018-12-21", "Character-Level NLP"),
    ("complement-objective-training-with-pytorch-lightning", "2021-06-23", "Complement Objective Training With PyTorch Lightning"),
    ("context-is-king", "2019-11-19", "Context Is King! Why Deep Learning Matters for NLP"),
    ("database-multi-tenancy", "2020-12-19", "Database Multi-Tenancy for SaaS"),
    ("efficiently-label-data-for-nlp", "2018-11-03", "Efficiently Labeling Data for NLP"),
    ("embrace-the-noise", "2018-11-03", "Embrace the Noise: A Case Study of Text Annotation for Medical Imaging"),
    ("how-to-label-data", "2019-06-01", "How to Label Data"),
    ("krippendorffs-alpha", "2020-05-03", "Simpledorff: Krippendorff's Alpha on DataFrames"),
    ("lighttag-acquired-by-primer", "2022-02-15", "LightTag Has Been Acquired by Primer.ai"),
    ("react-dc-js", "2019-02-10", "Using dc.js and Crossfilter With React"),
    ("sequence-labeling-with-transformers", "2020-09-18", "Sequence Labeling With Transformers"),
    ("snorql", "2021-02-08", "SnorQL: Scaling Weak Supervision With SQL"),
    ("spacy-vs-stanford", "2019-11-20", "Which Open-Source NER Model Is Best? Comparing CoreNLP, spaCy, and Flair"),
    ("unicode-surrogate-pairs", "2020-05-31", "JavaScript String Offsets and Unicode Surrogate Pairs"),
    ("postmortem-docker-swarm-wrong-tag", "2017-12-03", "Bug Postmortem: Wrong Image Deployed on Docker Swarm"),
    ("tensorflow-estimator-api", "2018-12-03", "Understanding the TensorFlow Estimator API"),
    ("fast-nlp-pretraining-with-vampire", "2020-04-26", "Fast NLP Model Pretraining With VAMPIRE"),
    ("when-to-use-machine-in-the-loop", "2019-02-05", "When Should You Use Machine in the Loop?"),
    ("code-to-align-annotations-with-huggingface-tokenizers", "2020-09-20", "Code to Align Annotations with Hugging Face Tokenizers"),
)

ANIMATIONS = (
    "character-level-nlp/openai-neural-sentiment.webp",
    "efficiently-label-data-for-nlp/example4.webp",
    "how-to-label-data/annotation-suggestions.webp",
    "how-to-label-data/create-annotation-task.webp",
    "how-to-label-data/document-classification-example.webp",
    "how-to-label-data/entity-annotation-example.webp",
    "how-to-label-data/pizza-relationship-annotation.webp",
    "how-to-label-data/relationship-annotation-example.webp",
    "how-to-label-data/relationship-search-example.webp",
    "react-dc-js/example.webp",
    "spacy-vs-stanford/reviewmode.webp",
)


def _repo_root() -> Path:
    """Return the repository root without depending on the process directory."""
    return Path(__file__).resolve().parents[3]


@pytest.mark.parametrize(("slug", "published", "title"), POSTS)
def test_lighttag_article_renders_with_provenance(
    page: Page, base_url: str, slug: str, published: str, title: str
) -> None:
    """Every archive record should retain its identity, date, notice, and media."""
    response = page.goto(f"{base_url}/en/posts/lighttag/{slug}/")
    assert response is not None and response.ok
    assert page.locator(".article-header h1").inner_text() == title

    timestamp = page.locator(".article-header time")
    assert timestamp.get_attribute("datetime") == published
    expected_date = date.fromisoformat(published).strftime("%b %-d, %Y").upper()
    assert timestamp.inner_text() == expected_date

    notice = page.locator("aside.original-publication")
    assert notice.count() == 1
    assert notice.inner_text() == "Originally published at LightTag.io."
    assert notice.locator("a").count() == 0

    image_sources: list[str] = page.locator("article img").evaluate_all(
        "images => images.map(image => image.currentSrc || image.src)"
    )
    for image_source in image_sources:
        image_response = page.request.get(image_source)
        assert image_response.ok, image_source
        assert image_response.headers["content-type"].startswith("image/"), image_source


def test_non_lighttag_article_has_no_archive_notice(page: Page, base_url: str) -> None:
    """Provenance rendering must be opt-in through front matter."""
    page.goto(f"{base_url}/en/posts/genai/learning-to-read-with-ai/")
    assert page.locator("aside.original-publication").count() == 0


def test_archive_has_no_defunct_lighttag_links(page: Page, base_url: str) -> None:
    """Rendered archive links should be third-party or valid local post links."""
    for slug, _, _ in POSTS:
        page.goto(f"{base_url}/en/posts/lighttag/{slug}/")
        assert page.locator("article a[href*='lighttag.io']").count() == 0
        assert page.locator("article a[href*='guide.lighttag.io']").count() == 0

        local_links = page.locator(".article-body a[href^='/en/posts/lighttag/']")
        for index in range(local_links.count()):
            href = local_links.nth(index).get_attribute("href")
            assert href is not None
            response = page.request.get(f"{base_url}{href}")
            assert response.ok, href


def test_archive_animations_and_webps_are_preserved() -> None:
    """Animations must keep frames and every WebP must remain under Git LFS."""
    archive = _repo_root() / "content/posts/lighttag"
    for relative_path in ANIMATIONS:
        with Image.open(archive / relative_path) as animation:
            assert animation.n_frames > 1, relative_path

    webps = sorted(archive.glob("**/*.webp"))
    relative_webps = [str(path.relative_to(_repo_root())) for path in webps]
    attributes = subprocess.run(
        ["git", "check-attr", "--stdin", "filter"],
        cwd=_repo_root(),
        input="\n".join(relative_webps),
        check=True,
        capture_output=True,
        text=True,
    )
    assert all(line.endswith(": filter: lfs") for line in attributes.stdout.splitlines())
