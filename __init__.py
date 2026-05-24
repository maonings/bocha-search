"""Bocha AI search plugin — register provider with Hermes."""

from __future__ import annotations

from .provider import BochaSearchProvider


def register(ctx) -> None:
    """Register the Bocha AI search provider."""
    ctx.register_web_search_provider(BochaSearchProvider())
