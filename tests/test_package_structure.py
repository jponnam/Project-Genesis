"""Structural tests for the Civitas Lab package layout.

These tests enforce the clean-architecture layer boundaries established
in Phase 1 Milestone 1. They verify that the package is importable,
that required layers exist, and that version metadata is well-formed.
"""

from __future__ import annotations

import importlib
from pathlib import Path

import civitas

REQUIRED_LAYERS: tuple[str, ...] = (
    "domain",
    "engine",
    "systems",
    "storage",
    "analytics",
    "cli",
)


def test_package_version_is_semver() -> None:
    """Package version must be a non-empty semantic version string."""
    parts = civitas.__version__.split(".")
    assert len(parts) == 3
    assert all(part.isdigit() for part in parts)
    assert civitas.__version__ == "0.1.0"


def test_package_docstring_describes_platform() -> None:
    """Root package docstring must identify Civitas Lab as a research platform."""
    assert civitas.__doc__ is not None
    lowered = civitas.__doc__.lower()
    assert "civitas lab" in lowered
    assert "research" in lowered


def test_required_layers_are_importable() -> None:
    """Every architectural layer must import as a subpackage."""
    for layer in REQUIRED_LAYERS:
        module = importlib.import_module(f"civitas.{layer}")
        assert module.__doc__ is not None
        assert module.__doc__.strip()


def test_src_layout_contains_all_layers() -> None:
    """Source tree must contain a directory for each architectural layer."""
    package_root = Path(civitas.__file__).resolve().parent
    for layer in REQUIRED_LAYERS:
        layer_path = package_root / layer
        assert layer_path.is_dir(), f"missing layer directory: {layer}"
        assert (layer_path / "__init__.py").is_file()


def test_layers_declare_no_cross_imports_in_init() -> None:
    """Layer __init__ modules must not import sibling layers.

    Coupling is forbidden at the package boundary. Systems communicate
    through domain events, not direct imports between layers.
    """
    package_root = Path(civitas.__file__).resolve().parent
    forbidden_prefixes = tuple(f"civitas.{layer}" for layer in REQUIRED_LAYERS)

    for layer in REQUIRED_LAYERS:
        init_path = package_root / layer / "__init__.py"
        source = init_path.read_text(encoding="utf-8")
        for prefix in forbidden_prefixes:
            if prefix == f"civitas.{layer}":
                continue
            assert f"import {prefix}" not in source
            assert f"from {prefix}" not in source
