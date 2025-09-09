from __future__ import annotations

import json
import re
import uuid
from typing import Dict, List, Tuple

from ..schemas import Card


def _safe_json_loads(text: str):
    try:
        return json.loads(text)
    except Exception:
        return None


def _extract_json_block(text: str):
    """Attempt to extract a JSON object from free-form text."""
    # Look for the first '{' and the last '}'
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = text[start : end + 1]
        parsed = _safe_json_loads(candidate)
        if parsed is not None:
            return parsed

    # Fallback: try to find a fenced code block with json
    fence = re.search(r"```json\s*([\s\S]*?)\s*```", text)
    if fence:
        candidate = fence.group(1)
        parsed = _safe_json_loads(candidate)
        if parsed is not None:
            return parsed

    return None


def parse_cards_from_text(text: str) -> Tuple[List[Card], Dict]:
    """Parse cards from model text. Returns (cards, meta)."""
    meta: Dict = {}
    parsed = _extract_json_block(text)

    if parsed and isinstance(parsed, dict) and "cards" in parsed:
        cards = []
        for idx, item in enumerate(parsed.get("cards", []) or []):
            # Robustly coerce to Card
            card = Card(
                id=str(item.get("id") or uuid.uuid4()),
                title=str(item.get("title") or f"Card {idx + 1}"),
                content=str(item.get("content") or ""),
                kind=str(item.get("kind") or "text"),
            )
            cards.append(card)
        if cards:
            return cards, meta

    # Fallback: create a single card with the whole text
    fallback = Card(
        id=str(uuid.uuid4()),
        title="Response",
        content=text.strip(),
        kind="text",
    )
    return [fallback], meta


def parse_followup_from_text(text: str) -> Card:
    parsed = _extract_json_block(text)
    if parsed and isinstance(parsed, dict) and "card" in parsed:
        item = parsed["card"]
        return Card(
            id=str(item.get("id") or uuid.uuid4()),
            title=str(item.get("title") or "Clarification"),
            content=str(item.get("content") or ""),
            kind=str(item.get("kind") or "text"),
        )

    return Card(
        id=str(uuid.uuid4()),
        title="Clarification",
        content=text.strip(),
        kind="text",
    )
