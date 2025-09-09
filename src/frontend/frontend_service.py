import os
from typing import Any, Dict

import requests
import streamlit as st
import yaml

BACKEND_URL = os.getenv("EASYGPT_BACKEND_URL", "http://localhost:8000")


class APIError(Exception):
    """Raised when an API request fails or cannot be completed."""


@st.cache_data
def load_config() -> Dict[str, Any]:
    """Load config.yaml once from the frontend folder."""
    cfg_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    if os.path.exists(cfg_path):
        with open(cfg_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def get_default_provider(config: Dict[str, Any]) -> str:
    """Return the default provider from config with sensible fallback."""
    return config.get("models", {}).get("default_provider", "mock")


def post_to_backend(path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Send a POST request to the backend API with consistent error handling."""
    url = f"{BACKEND_URL}{path}"
    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError as e:
        raise APIError("❌ Cannot connect to the backend. Please ensure the backend server is running.") from e
    except requests.exceptions.Timeout as e:
        raise APIError("⏱️ Request timed out. The server might be busy. Please try again.") from e
    except requests.exceptions.HTTPError as e:
        try:
            detail = e.response.json().get("detail", e.response.text)
        except ValueError:
            detail = e.response.text
        if "API key" in str(detail):
            raise APIError("🔑 API key error. Please check your configuration or select the 'mock' provider.") from e
        raise APIError(f"❌ An error occurred: {detail}") from e
    except Exception as e:
        raise APIError(f"An unexpected error occurred: {e}") from e


def create_generate_payload(prompt: str, provider: str, model: str) -> Dict[str, Any]:
    """Build request payload for generate endpoint."""
    return {"prompt": prompt, "provider": provider, "model": model}


def create_followup_payload(
    current_card_title: str,
    current_card_content: str,
    question: str,
    provider: str,
    model: str,
) -> Dict[str, Any]:
    """Build request payload for follow-up endpoint."""
    return {
        "current_card_title": current_card_title,
        "current_card_content": current_card_content,
        "question": question,
        "provider": provider,
        "model": model,
    }


def init_session_state() -> None:
    """Ensure required Streamlit session state keys exist."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "card_nav" not in st.session_state:
        st.session_state.card_nav = {"index": 0, "view_all": False}


def reset_card_nav() -> None:
    """Reset step navigation state to the first card and hide 'view all'."""
    st.session_state.card_nav = {"index": 0, "view_all": False}


def append_user_message(prompt: str) -> None:
    """Append a user message to chat history."""
    st.session_state.messages.append({"role": "user", "content": prompt})


def append_assistant_message(content: Any, is_error: bool = False) -> None:
    """Append an assistant message to chat history."""
    if is_error:
        st.session_state.messages.append({"role": "assistant", "content": content, "error": True})
    else:
        st.session_state.messages.append({"role": "assistant", "content": content})


def handle_generate(prompt: str, provider: str, model: str) -> None:
    """Handle the full generate flow: state transitions and API call."""
    append_user_message(prompt)
    reset_card_nav()
    try:
        payload = create_generate_payload(prompt, provider, model)
        response_data = post_to_backend("/v1/generate", payload)
        append_assistant_message(response_data)
    except APIError as e:
        append_assistant_message(str(e), is_error=True)


def ask_followup(
    current_card_title: str,
    current_card_content: str,
    question: str,
    provider: str,
    model: str,
) -> Dict[str, Any]:
    """Send a follow-up question about the current step to the backend."""
    payload = create_followup_payload(current_card_title, current_card_content, question, provider, model)
    return post_to_backend("/v1/followup", payload)


