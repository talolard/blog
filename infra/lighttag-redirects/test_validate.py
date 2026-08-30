"""Offline regression tests for the LightTag redirect validator."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest


def _validator() -> ModuleType:
    """Load the script as a module without installing the repository."""
    path = Path(__file__).with_name("validate.py")
    spec = importlib.util.spec_from_file_location("lighttag_redirect_validator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


validator = _validator()


def test_front_matter_is_the_single_source_of_truth() -> None:
    """Every imported article yields exactly one unique redirect pair."""
    pairs = validator.derive_expected_pairs()
    assert len(pairs) == 23
    assert len({pair.source for pair in pairs}) == 23
    assert len({pair.destination for pair in pairs}) == 23
    assert any(pair.source == "/blog/active-learning-optimization-is-not-imporvement" for pair in pairs)
    assert any(pair.source == "/blog/character-level-nlp" for pair in pairs)
    assert any(pair.source == "/blog/sequence-labeling-with-transformers/example" for pair in pairs)
    assert any(pair.source == "/how-to-label-data" for pair in pairs)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("/BLOG/Character-Level-NLP/", "/blog/character-level-nlp"),
        ("//blog//snorql///", "/blog/snorql"),
        ("/how-to-label-data/?utm_source=old", "/how-to-label-data"),
        ("", "/"),
        ("guide", "/guide"),
    ],
)
def test_path_normalization(raw: str, expected: str) -> None:
    """Case, repeated separators, and trailing slashes normalize predictably."""
    assert validator.normalize_path(raw) == expected


def test_function_probe_variants_include_internal_slash_and_index() -> None:
    """The application probe set exercises CloudFront's URI normalization."""
    variants = validator._path_variants("/blog/snorql")
    assert "/blog//snorql" in variants
    assert "/blog/snorql/index.html" in variants


def test_template_function_executes_every_mapping() -> None:
    """The exact template code must satisfy mappings and canonical query dropping."""
    assert validator.validate_local() == []


def test_local_validation_does_not_resolve_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Default validation remains deterministic and offline."""
    def fail(*args: str, **kwargs: str) -> None:
        raise AssertionError("network access is not allowed in local mode")

    monkeypatch.setattr(validator.socket, "getaddrinfo", fail)
    monkeypatch.setattr(validator.socket, "create_connection", fail)
    monkeypatch.setattr(validator.socket.socket, "connect", fail)
    assert validator.validate_local() == []
