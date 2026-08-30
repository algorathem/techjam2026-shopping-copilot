"""Optional LLM semantic rerank of a short candidate list.

Official scoring may disable network, so this is gated on XAI_API_KEY and
never required. Failures return None and the caller keeps lexical order.

Uses SpaceXAI (xAI) OpenAI-compatible chat completions via stdlib urllib.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request


API_URL = "https://api.x.ai/v1/chat/completions"
DEFAULT_MODEL = os.environ.get("SHOPPILOT_LLM_MODEL", "grok-4.5")


def llm_enabled() -> bool:
    return bool(os.environ.get("XAI_API_KEY")) and os.environ.get("SHOPPILOT_LLM", "0") == "1"


def rerank(brief: str, candidates: list[dict], top_k: int = 10) -> tuple[list[str] | None, int, int]:
    """Return (asin_order, prompt_tokens, completion_tokens) or (None, 0, 0)."""
    key = os.environ.get("XAI_API_KEY")
    if not key or not candidates:
        return None, 0, 0
    lines = []
    for idx, item in enumerate(candidates, start=1):
        title = str(item.get("title") or "")[:140]
        store = str(item.get("store") or "")[:40]
        asin = item["parent_asin"]
        lines.append(f"{idx}. {asin} | {store} | {title}")
    user = (
        "Shopper need:\n"
        f"{brief}\n\n"
        "Candidates (best match first). Return ONLY a JSON array of parent_asin "
        "strings, most relevant first, no extras.\n"
        + "\n".join(lines)
    )
    payload = {
        "model": DEFAULT_MODEL,
        "temperature": 0,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You rerank catalog products for a shopping assistant. "
                    "Prefer exact attribute matches (material, color, category) "
                    "over popularity. Output a JSON array of parent_asin only."
                ),
            },
            {"role": "user", "content": user},
        ],
    }
    request = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=12) as response:
            body = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError):
        return None, 0, 0
    usage = body.get("usage") or {}
    prompt_tokens = int(usage.get("prompt_tokens") or 0)
    completion_tokens = int(usage.get("completion_tokens") or 0)
    try:
        content = body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        return None, prompt_tokens, completion_tokens
    order = _parse_asins(content, {c["parent_asin"] for c in candidates})
    if not order:
        return None, prompt_tokens, completion_tokens
    return order[:top_k], prompt_tokens, completion_tokens


def _parse_asins(content: str, allowed: set[str]) -> list[str]:
    text = content.strip()
    start = text.find("[")
    end = text.rfind("]")
    blob = text[start : end + 1] if start >= 0 and end > start else text
    try:
        parsed = json.loads(blob)
    except json.JSONDecodeError:
        parsed = [part.strip(" \"',") for part in text.replace("\n", ",").split(",")]
    ordered: list[str] = []
    seen: set[str] = set()
    if isinstance(parsed, list):
        values = parsed
    else:
        values = []
    for item in values:
        asin = str(item).strip()
        if asin in allowed and asin not in seen:
            seen.add(asin)
            ordered.append(asin)
    return ordered
