import os
from typing import Any, Dict, List

import requests
import streamlit as st
import yaml
from html import escape

# --- CONFIGURATION & CONSTANTS ---

# Load configuration
BACKEND_URL = os.getenv("EASYGPT_BACKEND_URL", "http://localhost:8000")
DEFAULT_EXAMPLE_QUERY = "How do I make a grilled cheese sandwich?"
PROGRAMMING_EXAMPLE_QUERY = "I have windows 11 and i want to install python on my machine. How do i do that?"

@st.cache_data
def load_config() -> Dict[str, Any]:
    """Load config.yaml once from the frontend folder."""
    cfg_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    if os.path.exists(cfg_path):
        with open(cfg_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}

CONFIG = load_config()

# --- API COMMUNICATION ---

class APIError(Exception):
    """Custom exception for user-friendly API error messages."""
    pass

def post_to_backend(path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sends a POST request to the backend and handles errors gracefully.

    Args:
        path: The API endpoint path (e.g., "/v1/generate").
        payload: The JSON payload to send.

    Returns:
        The JSON response from the backend.

    Raises:
        APIError: If the request fails for any reason.
    """
    url = f"{BACKEND_URL}{path}"
    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)
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

# --- UI RENDERING COMPONENTS ---

def inject_css():
    """Injects custom CSS from styles.css into the Streamlit app."""
    css_path = os.path.join(os.path.dirname(__file__), "styles.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def render_sidebar() -> tuple[str, str]:
    """Renders the settings sidebar and returns the selected provider and model."""
    with st.sidebar:
        st.header("⚙️ Settings")

        cfg_models = CONFIG.get("models", {})
        cfg_providers = cfg_models.get("providers", {})
        providers = list(cfg_providers.keys()) or ["mock"]
        default_provider = cfg_models.get("default_provider", "mock")
        provider_index = providers.index(default_provider) if default_provider in providers else 0

        provider = st.selectbox(
            "AI Provider",
            options=providers,
            index=provider_index,
            help="Select your preferred AI provider."
        )

        provider_models = cfg_providers.get(provider, [])
        first_model = provider_models[0] if provider_models else "mock-model"
        model = st.selectbox(
            "Model",
            options=[first_model],
            index=0,
            help="Model is fixed to the first configured for the provider.",
        )

        st.divider()

        # --- Example buttons with tooltips ---
        if st.button(
            "🥪 Run Cooking Example Query",
            help="See how to make a grilled cheese sandwich step by step",
            use_container_width=True
        ):
            st.session_state.run_example = True
            st.session_state.example_query = DEFAULT_EXAMPLE_QUERY

        if st.button(
            "💻 Run Tech Example Query",
            help="Learn how to install Python on Windows 11",
            use_container_width=True
        ):
            st.session_state.run_example = True
            st.session_state.example_query = PROGRAMMING_EXAMPLE_QUERY
            
    return provider, model

def render_response_controls(cards: List[Dict[str, Any]]):
    """Renders navigation buttons for stepping through response cards."""
    nav_state = st.session_state.card_nav
    total_cards = len(cards)
    
    if total_cards <= 1:
        return

    def set_card_index(delta: int):
        nav_state["index"] += delta
        nav_state["view_all"] = False

    def toggle_view_all():
        nav_state["view_all"] = not nav_state["view_all"]

    st.write(f"Step {nav_state['index'] + 1} of {total_cards}")
    
    cols = st.columns(3)
    with cols[0]:
        st.button(
            "⬅️ Previous", 
            on_click=set_card_index, 
            args=(-1,), 
            disabled=(nav_state["index"] <= 0),
            use_container_width=True
        )
    with cols[1]:
        st.button(
            "Next ➡️", 
            on_click=set_card_index, 
            args=(1,), 
            disabled=(nav_state["index"] >= total_cards - 1),
            use_container_width=True
        )
    with cols[2]:
        view_all_text = "📋 Hide All" if nav_state["view_all"] else "🔍 View All"
        st.button(view_all_text, on_click=toggle_view_all, use_container_width=True)

def render_followup_section(current_card: Dict[str, Any], provider: str, model: str):
    """Renders the input for asking a follow-up question about a specific step."""
    st.divider()
    
    followup_key = f"followup_input_{current_card.get('id', 'card')}"
    question = st.text_input(
        "Ask a question about this step:",
        placeholder="Type your clarifying question here...",
        key=followup_key,
    )
    
    if st.button("Ask Follow-up", type="primary"):
        if question.strip():
            payload = {
                "current_card_title": current_card.get("title", ""),
                "current_card_content": current_card.get("content", ""),
                "question": question.strip(),
                "provider": provider,
                "model": model,
            }
            with st.spinner("Thinking..."):
                try:
                    data = post_to_backend("/v1/followup", payload)
                    st.info("Follow-up Answer:")
                    card = data.get("card", {})
                    if card.get("title"):
                        st.subheader(card["title"])
                    if card.get("content"):
                        st.markdown(card["content"])
                except APIError as e:
                    st.error(str(e))
        else:
            st.warning("Please enter a follow-up question.")

def render_assistant_message(response: Dict[str, Any], provider: str, model: str):
    """
    Renders the assistant's response, including cards, navigation, and follow-up options.
    """
    nav_state = st.session_state.card_nav
    cards = response.get("cards", [])

    if not cards:
        st.info("I couldn't generate a step-by-step guide for that. Please try another question.")
        return

    if nav_state["view_all"]:
        st.subheader("All Steps Overview")
        for i, card in enumerate(cards):
            if card.get("title"):
                st.write(f"**Step {i + 1}:** {card.get('title', '')}")
            if card.get("content"):
                st.markdown(card.get('content', ''))
            if i < len(cards) - 1:
                st.divider()
    else:
        card_idx = max(0, min(nav_state["index"], len(cards) - 1))
        nav_state["index"] = card_idx
        current_card = cards[card_idx]
        
        if current_card.get("title"):
            st.subheader(current_card["title"])
        if current_card.get("content"):
            st.markdown(current_card["content"])
        
        render_followup_section(current_card, provider, model)

    render_response_controls(cards)

# --- MAIN APPLICATION LOGIC ---

def main():
    """The main function that runs the Streamlit application."""
    st.set_page_config(
        page_title="EasyGPT", 
        page_icon="✨", 
        layout="wide",
        menu_items={},  # This removes the three-dot menu
        initial_sidebar_state="expanded"
    )
    
    # Hide the deploy button and menu
    hide_elements = """
        <style>
            #MainMenu {visibility: hidden;}
            .stDeployButton {display: none;}
            header {visibility: hidden;}
            footer {visibility: hidden;}
            .block-container {
                padding-top: 1rem;
                padding-bottom: 0rem;
            }
        </style>
    """
    st.markdown(hide_elements, unsafe_allow_html=True)
    inject_css()

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "card_nav" not in st.session_state:
        st.session_state.card_nav = {"index": 0, "view_all": False}

    # Create sticky header with title and tagline
    st.markdown("""
        <div class="sticky-header">
            <h1>✨ EasyGPT</h1>
            <p>Your AI-powered step-by-step guide</p>
        </div>
        """, unsafe_allow_html=True)

    provider, model = render_sidebar()

    def process_prompt(prompt: str):
        """Shared logic to handle prompt submission."""
        # Reset chat history so only the current request/response are kept
        st.session_state.messages = [{"role": "user", "content": prompt}]
        st.session_state.card_nav = {"index": 0, "view_all": False}
        
        with st.spinner("Generating steps..."):
            try:
                payload = {"prompt": prompt, "provider": provider, "model": model}
                response_data = post_to_backend("/v1/generate", payload)
                st.session_state.messages.append({"role": "assistant", "content": response_data})
            except APIError as e:
                st.session_state.messages.append({"role": "assistant", "content": str(e), "error": True})
        st.rerun()

    # --- Process example prompt if triggered ---
    if st.session_state.get("run_example"):
        example_query = st.session_state.get("example_query", DEFAULT_EXAMPLE_QUERY)
        st.session_state.run_example = False  # Reset flag
        st.session_state.example_query = None  # Reset query
        process_prompt(example_query)

    # --- Welcome Message (if chat is empty) ---
    if not st.session_state.messages:
        st.info("Ask me how to do something, and I'll break it down for you!")
    # --- Chat History Display ---
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "user":
                cols = st.columns([0.3, 0.7])
                with cols[1]:
                    st.markdown(
                        f'<div class="easygpt-user-wrap"><div class="easygpt-user-bubble">{escape(str(message["content"]))}</div></div>',
                        unsafe_allow_html=True,
                    )
            elif message["role"] == "assistant":
                cols = st.columns([0.7, 0.3])
                with cols[0]:
                    if "error" in message:
                        st.error(message["content"])
                    else:
                        with st.container(border=True):
                            render_assistant_message(message["content"], provider, model)

    # --- Persistent Chat Input at the bottom ---
    if prompt := st.chat_input("How do I...?"):
        process_prompt(prompt)

if __name__ == "__main__":
    main()  