from __future__ import annotations

from typing import Optional


CARDS_JSON_INSTRUCTION = (
    "You are a helpful assistant. Respond ONLY with valid JSON in the schema: "
    "{\n  \"cards\": [\n    {\n      \"id\": \"string\",\n      \"title\": \"string\",\n      \"content\": \"string\",\n      \"kind\": \"text\"\n    }\n  ]\n}. "
    "Do not include any surrounding prose. Keep titles short and content concise."
)


FOLLOWUP_JSON_INSTRUCTION = (
    "You are answering a clarifying question about a specific card. "
    "Respond ONLY with valid JSON in the schema: "
    "{\n  \"card\": {\n    \"id\": \"string\",\n    \"title\": \"string\",\n    \"content\": \"string\",\n    \"kind\": \"text\"\n  }\n}. "
    "The response should be a single short paragraph directly addressing the question."
)


def build_cards_system_prompt(user_system: Optional[str] = None) -> str:
    if user_system:
        return f"{user_system}\n\n{CARDS_JSON_INSTRUCTION}"
    return CARDS_JSON_INSTRUCTION


def build_followup_system_prompt(
    current_card_title: str, current_card_content: str, user_system: Optional[str] = None
) -> str:
    context = (
        "Context for this clarifying question: "
        f"The current step is '{current_card_title}'. "
        f"Content: '{current_card_content}'."
    )
    if user_system:
        return f"{user_system}\n\n{context}\n\n{FOLLOWUP_JSON_INSTRUCTION}"
    return f"{context}\n\n{FOLLOWUP_JSON_INSTRUCTION}"
