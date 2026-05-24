"""Bocha AI (博查) web search provider.

Subclasses :class:`agent.web_search_provider.WebSearchProvider`.
Registered via ``ctx.register_web_search_provider()``, activated by
setting ``web.backend: bocha-search`` in config.yaml.

API: POST https://api.bochaai.com/v1/web-search
Auth: Authorization: Bearer <BOCHA_API_KEY>
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict

import httpx

from agent.web_search_provider import WebSearchProvider

logger = logging.getLogger(__name__)

BOCHA_API_URL = "https://api.bochaai.com/v1/web-search"


class BochaSearchProvider(WebSearchProvider):
    """Bocha AI web search — search-only, no extract/crawl."""

    @property
    def name(self) -> str:
        return "bocha-search"

    @property
    def display_name(self) -> str:
        return "Bocha AI (博查)"

    def is_available(self) -> bool:
        return bool((os.getenv("BOCHA_API_KEY") or "").strip())

    def supports_search(self) -> bool:
        return True

    def supports_extract(self) -> bool:
        return False

    def search(self, query: str, limit: int = 5) -> Dict[str, Any]:
        api_key = (os.getenv("BOCHA_API_KEY") or "").strip()
        if not api_key:
            return {"success": False, "error": "BOCHA_API_KEY is not set"}

        safe_limit = max(1, min(int(limit), 20))

        body: Dict[str, Any] = {
            "query": query,
            "count": safe_limit,
            "summary": False,
        }

        try:
            resp = httpx.post(
                BOCHA_API_URL,
                json=body,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                timeout=15,
            )
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.warning("Bocha HTTP %d: %s", exc.response.status_code, exc.response.text[:300])
            return {"success": False, "error": f"Bocha returned HTTP {exc.response.status_code}"}
        except httpx.RequestError as exc:
            logger.warning("Bocha request error: %s", exc)
            return {"success": False, "error": f"Could not reach Bocha API: {exc}"}

        try:
            data = resp.json()
        except Exception:
            return {"success": False, "error": "Bocha response is not valid JSON"}

        pages = data.get("data", {}).get("webPages", {}).get("value", [])
        if not pages:
            pages = data.get("data", {}).get("pages", [])

        results = []
        for i, page in enumerate(pages[:safe_limit]):
            results.append({
                "title": str(page.get("name", page.get("title", ""))),
                "url": str(page.get("url", "")),
                "description": str(page.get("snippet", page.get("summary", ""))),
                "position": i + 1,
            })

        logger.info("Bocha search '%s': %d results (limit %d)", query, len(results), safe_limit)
        return {"success": True, "data": {"web": results}}

    def get_setup_schema(self) -> Dict[str, Any]:
        return {
            "name": "Bocha AI (博查)",
            "badge": "free tier · search only",
            "tag": "Chinese AI search engine — free daily quota, API key required",
            "env_vars": [
                {
                    "key": "BOCHA_API_KEY",
                    "prompt": "Bocha API key",
                    "url": "https://open.bochaai.com/dashboard",
                },
            ],
        }
