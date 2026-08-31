"""Optional light-LLM slot / dual-meaning normalizer.

Modes (requires SHOPPILOT_LLM=1 and GEMINI_API_KEY or XAI_API_KEY):
  SHOPPILOT_LLM_SLOTS=off       default — no calls
  SHOPPILOT_LLM_SLOTS=always    one JSON parse call every user turn
  SHOPPILOT_LLM_SLOTS=lowconf   call only when rule-based confidence is low

Output is validated against the official ask_attribute enum (+ internal
family/audience). Failures return None; caller keeps regex/lexicon state.

Never commit API keys.
"""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request

from starter.llm_rerank import GEMINI_DEFAULT_MODEL, XAI_API_URL, XAI_DEFAULT_MODEL, llm_enabled

ALLOWED_SLOTS = frozenset(
    {
        "category",
        "material",
        "color",
        "size",
        "style",
        "brand",
        "budget",
        "feature",
        "use_case",
        "other",
    }
)
ALLOWED_FAMILY = frozenset(
    {
        "dress",
        "footwear",
        "top",
        "bottom",
        "outerwear",
        "bag",
        "jewelry",
        "belt",
        "hat",
    }
)
ALLOWED_AUDIENCE = frozenset({"men", "women", "boys", "girls", "unisex_kids"})


def llm_slots_mode() -> str:
    """off | always | lowconf"""
    if not llm_enabled():
        return "off"
    mode = (os.environ.get("SHOPPILOT_LLM_SLOTS") or "off").strip().lower()
    if mode in {"1", "true", "yes", "on"}:
        return "always"
    if mode in {"always", "lowconf", "off", "0", "false", "no"}:
        if mode in {"0", "false", "no"}:
            return "off"
        return mode
    return "off"


def llm_rerank_enabled() -> bool:
    """Rerank is separate from slot NLU so you can A/B them independently."""
    if not llm_enabled():
        return False
    return os.environ.get("SHOPPILOT_LLM_RERANK", "0") == "1"


def rule_nlu_confidence(
    message: str,
    *,
    family: str | None,
    audience: str | None,
    n_new_constraints: int,
    filled_before: int,
) -> float:
    """Heuristic 0..1: how confident the deterministic path is.

    Low → dual meanings / vague vibe / long multi-intent freeform.
    High → short answers, kit disclosures, clear size/color/material.
    """
    text = (message or "").strip()
    if not text:
        return 1.0
    lowered = text.lower()
    score = 0.55

    # Kit / simulator patterns are already structured.
    if re.search(r"key requirement is|what matters is|don'?t have (?:a |an additional )?preference", lowered):
        score += 0.35
    if re.search(r"^i(?:'m| am) looking for\b", lowered):
        score += 0.15

    # Explicit audience / family already captured.
    if audience:
        score += 0.12
    if family:
        score += 0.08

    # Clear single-slot answers.
    if len(lowered) <= 24 and n_new_constraints >= 1:
        score += 0.2
    if n_new_constraints >= 2:
        score += 0.1
    if filled_before >= 3 and n_new_constraints >= 1:
        score += 0.05

    # Ambiguity / dual-meaning cues → lower confidence.
    dual_cues = (
        r"\bdress\s+(shoes|sandals|boots|sneakers)\b",
        r"\b(cool|light|soft|classic|clean|sharp|fresh)\b",
        r"\b(for\s+my\s+\w+|gift\s+for)\b",
        r"\b(something|anything|vibes?|aesthetic|kinda|sort of|ish)\b",
        r"\b(and|but|also)\b.+\b(and|but|also)\b",
    )
    for pat in dual_cues:
        if re.search(pat, lowered):
            score -= 0.18

    if len(lowered) > 80 and n_new_constraints == 0:
        score -= 0.25
    if len(lowered) > 40 and n_new_constraints == 0 and not re.search(
        r"looking for|requirement|matters is|preference", lowered
    ):
        score -= 0.2

    return max(0.0, min(1.0, score))


def should_call_slots_llm(
    mode: str,
    message: str,
    *,
    family: str | None,
    audience: str | None,
    n_new_constraints: int,
    filled_before: int,
    threshold: float | None = None,
) -> tuple[bool, float]:
    conf = rule_nlu_confidence(
        message,
        family=family,
        audience=audience,
        n_new_constraints=n_new_constraints,
        filled_before=filled_before,
    )
    if mode == "off":
        return False, conf
    if mode == "always":
        return True, conf
    if mode == "lowconf":
        thr = threshold if threshold is not None else float(
            os.environ.get("SHOPPILOT_LLM_SLOTS_THRESHOLD", "0.55")
        )
        return conf < thr, conf
    return False, conf


def parse_slots_llm(
    message: str,
    *,
    category: str = "",
    family: str | None = None,
    audience: str | None = None,
    filled: list[str] | None = None,
    last_ask: str | None = None,
) -> tuple[dict | None, int, int]:
    """Return (parse_dict, prompt_tokens, completion_tokens) or (None, 0, 0)."""
    if not message or not message.strip():
        return None, 0, 0
    if llm_slots_mode() == "off":
        return None, 0, 0

    system = (
        "You are a shopping-dialogue slot normalizer. "
        "Resolve dual meanings (e.g. dress garment vs dress shoes; cool vibe vs cool fabric; "
        "kids audience vs size). "
        "Return ONLY JSON with keys: "
        "family (string|null), audience (string|null), "
        "slots (array of {attr, value, p}), notes (string). "
        f"attr must be one of: {sorted(ALLOWED_SLOTS)}. "
        f"family one of: {sorted(ALLOWED_FAMILY)} or null. "
        f"audience one of: {sorted(ALLOWED_AUDIENCE)} or null. "
        "p is confidence 0..1. Prefer precision over recall. "
        "Do not invent brands. Empty slots array is allowed."
    )
    user = (
        f"utterance: {message}\n"
        f"category_so_far: {category or ''}\n"
        f"family_so_far: {family or ''}\n"
        f"audience_so_far: {audience or ''}\n"
        f"filled_slots: {filled or []}\n"
        f"last_ask_attribute: {last_ask or ''}\n"
        "JSON:"
    )

    gemini_key = os.environ.get("GEMINI_API_KEY")
    if gemini_key:
        raw, pt, ct = _chat_gemini(system, user, gemini_key)
    else:
        xai_key = os.environ.get("XAI_API_KEY")
        if not xai_key:
            return None, 0, 0
        raw, pt, ct = _chat_xai(system, user, xai_key)

    if not raw:
        return None, pt, ct
    parsed = _parse_slot_json(raw)
    if not parsed:
        if os.environ.get("SHOPPILOT_LLM_DEBUG") == "1":
            print(f"[llm_slots] parse fail raw={raw[:240]!r}")
        return None, pt, ct
    return parsed, pt, ct


def apply_slot_parse(state, parsed: dict, *, min_p: float = 0.55) -> int:
    """Merge validated LLM parse into SessionState. Returns #slots applied."""
    if not parsed:
        return 0
    applied = 0
    thr = float(os.environ.get("SHOPPILOT_LLM_SLOTS_MIN_P", str(min_p)))

    family = parsed.get("family")
    if isinstance(family, str) and family in ALLOWED_FAMILY:
        state.product_family = family

    audience = parsed.get("audience")
    if isinstance(audience, str) and audience in ALLOWED_AUDIENCE:
        state.audience = audience
        label = {
            "men": "men's",
            "women": "women's",
            "boys": "boys",
            "girls": "girls",
            "unisex_kids": "kids",
        }.get(audience, audience)
        # Soft constraint for FTS; avoid dup spam.
        if label.lower() not in {c.lower() for c in state.constraints}:
            state.add_constraint(label, source="soft")
            applied += 1

    slots = parsed.get("slots") or []
    if not isinstance(slots, list):
        return applied
    for item in slots:
        if not isinstance(item, dict):
            continue
        attr = str(item.get("attr") or "").strip().lower()
        value = str(item.get("value") or "").strip()
        try:
            p = float(item.get("p", 0.0))
        except (TypeError, ValueError):
            p = 0.0
        if attr not in ALLOWED_SLOTS or attr == "other":
            continue
        if p < thr or len(value) < 2:
            continue
        # Prefer short values; long kit blobs already handled by rules.
        if len(value) > 80:
            value = value[:80]
        state.add_constraint(value, source="soft")
        state.filled.add(attr)
        applied += 1
    return applied


def _chat_gemini(system: str, user: str, key: str) -> tuple[str | None, int, int]:
    model = os.environ.get("SHOPPILOT_GEMINI_MODEL", GEMINI_DEFAULT_MODEL)
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{urllib.parse.quote(model, safe='')}:generateContent"
        f"?key={urllib.parse.quote(key, safe='')}"
    )
    payload = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "generationConfig": {
            "temperature": 0,
            "maxOutputTokens": 512,
            "responseMimeType": "application/json",
        },
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=18) as response:
            body = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError) as exc:
        if os.environ.get("SHOPPILOT_LLM_DEBUG") == "1":
            print(f"[llm_slots] gemini error: {type(exc).__name__}: {exc}")
        return None, 0, 0
    usage = body.get("usageMetadata") or {}
    pt = int(usage.get("promptTokenCount") or 0)
    ct = int(usage.get("candidatesTokenCount") or 0)
    try:
        parts = body["candidates"][0]["content"]["parts"]
        content = "".join(str(p.get("text") or "") for p in parts)
    except (KeyError, IndexError, TypeError):
        return None, pt, ct
    return content, pt, ct


def _chat_xai(system: str, user: str, key: str) -> tuple[str | None, int, int]:
    payload = {
        "model": XAI_DEFAULT_MODEL,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    request = urllib.request.Request(
        XAI_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            body = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError):
        return None, 0, 0
    usage = body.get("usage") or {}
    pt = int(usage.get("prompt_tokens") or 0)
    ct = int(usage.get("completion_tokens") or 0)
    try:
        content = body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        return None, pt, ct
    return content, pt, ct


def _parse_slot_json(content: str) -> dict | None:
    text = content.strip()
    if "```" in text:
        text = text.replace("```json", "```").replace("```", "\n")
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        data = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    return data
