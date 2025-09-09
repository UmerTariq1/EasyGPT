# EasyGPT MVP: Technical Report

## 1. Architectural Overview

The proposed architecture follows a client-server model, separating the user interface (front-end) from the core logic and AI interactions (back-end).

**Front-end (Streamlit):**
- Handles all user interaction and the display of information.
- Manages conversation state using `st.session_state`.
- Renders content in a custom, card-based format using Streamlit's native components and custom CSS.

**Back-end (FastAPI):**
- Lightweight API that accepts user queries, interacts with the LLM API, and returns a structured response.
- Central hub for all LLM-related logic.

The two components communicate via a single REST API endpoint, allowing independent development, testing, and deployment.

### Why a Separate Backend is Necessary

- **Security:** Placing the LLM API key in the front-end would expose it to users. The FastAPI backend acts as a secure proxy, keeping the API key on the server.
- **Separation of Concerns:** Backend holds core business logic (prompt engineering, API key management); front-end is responsible for UI. This makes codebases cleaner and more maintainable.
- **Scalability:** Decoupled architecture allows independent scaling of front-end and back-end.

## 2. High-Level Plan

1. **Define a Structured Output Schema:** Design a clear JSON schema for the LLM to follow, forming the foundation of the card-based UI.
2. **Build the FastAPI Back-end:** Create an API endpoint that accepts user prompts, calls the LLM with system/user messages (instructing JSON output), and returns the parsed JSON response.
3. **Build the Streamlit Front-end:** Create a chat interface that sends user input to the FastAPI back-end and receives JSON responses, dynamically generating "cards" on the screen.
4. **Add Custom CSS:** Style the Streamlit app to match the EasyGPT product vision.

## 3. Core Logic: Handling Hierarchical Content and State

The goal is to present a single step to the user at a time, allowing navigation and clarifying questions in the context of the current step.

### Implementation Strategy

- **State Management with `st.session_state`:**
	- `st.session_state.conversation_history`: Full history of user prompts and LLM multi-card responses.
	- `st.session_state.current_response_index`: Tracks which multi-card response is displayed.
	- `st.session_state.current_card_index`: Tracks which card within the current response is displayed.

#### User Actions and State Changes

- **Initial Prompt:** Calls FastAPI backend, saves full response to `conversation_history`, resets indices.
- **"Next" Button:** Increments `current_card_index` to show the next card.
- **"Back" Button:** Decrements `current_card_index` to show the previous card.
- **Follow-up Question:** Sends new request to backend with the current card's text and context for a relevant, nested response.

#### Backend Logic for Follow-up Questions

- New API endpoint accepts the new prompt and current card content.
- Prompt to LLM includes system instruction, current step context, and user question.

**Prompt Example:**
```
System Instruction: "You are a helpful assistant providing a clarifying response. The user has a question about a specific step. Your response should be a single, short paragraph that directly answers their question, referencing the provided context. Do not generate a new series of steps."
Context: The current step the user is on is: '{current_card_title}': '{current_card_content}'
User Question: '{user_followup_question}'
```

## 4. The Core UI Concept: The Card

The fundamental unit of the EasyGPT UI is the card—a simple, clean, self-contained container for a single piece of information, instruction, or question.

- **Main Screen:** Shows one card at a time, reducing clutter and focusing attention.
- **Simple Controls:**
	- "Next" to move forward
	- "Back" to return
	- "View All" to see the entire conversation or all steps
	- **Contextual Input Box:** For questions about the current card's content

### Hierarchical & Dynamic Flow

- **Guided Instructions (Linear Path):**
	- User asks, "How do I make a grilled cheese sandwich?"
	- Card 1: "Ingredients" list
	- Card 2: "Step 1: Preparation" instructions
	- User navigates with Next/Back
- **Nested Conversations (Drilling Down):**
	- User asks a clarifying question on a card (e.g., "What kind of cheese should I use?")
	- AI response is shown within the context of that card, possibly as a nested pop-up or temporary card
- **Consultation Mode (Q&A):**
	- User asks, "What perfume should I buy?"
	- Card 1: AI asks about scent preference
	- Card 2: AI asks about occasion
	- Continues until enough info is gathered for a recommendation

### Overall Aesthetic

- **Minimalist Design:** Clean, uncluttered pages focused on a single content element
- **Large, Legible Text:** Adjustable font size, clear typography
- **High Contrast:** Color scheme for readability
- **Simple Visual Cues:** Icons and cues to guide users

## 5. File and Project Structure

A simple, extensible project structure is recommended for this MVP:

```plaintext
/easygpt-project
├── src/
│   ├── backend/
│   │   ├── main.py           # FastAPI application and API endpoint
│   │   ├── schemas.py        # Pydantic models for request/response validation
│   │   └── requirements.txt  # Back-end dependencies
│   └── frontend/
│       ├── app.py            # Streamlit application and UI logic
│       ├── styles.css        # Custom CSS for the front-end
│       └── requirements.txt  # Front-end dependencies
└── .env                      # Environment variables (e.g., API keys)
```
