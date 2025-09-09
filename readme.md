[![Technical Architecture](https://img.shields.io/badge/Technical_Architecture-Read-0A66C2?style=for-the-badge)](docs//technical%20architecture.md)
[![Product Details](https://img.shields.io/badge/Product_Details-Read-4CAF50?style=for-the-badge)](docs//product_details.md)

# EasyGPT

## What is EasyGPT?
EasyGPT is a clean, step‑by‑step AI assistant. Instead of wall‑of‑text answers, it breaks tasks into simple, navigable cards you can move through with Next/Back and ask focused follow‑up questions.

## Why it’s different
- **Card-based guidance**: Clear steps instead of long paragraphs
- **Focused follow-ups**: Ask questions about the current step in context
- **Provider-agnostic**: Works with multiple LLM providers (mock/OpenAI/Gemini/DeepSeek via config)
- **Secure by design**: Frontend (Streamlit) and backend (FastAPI) are split; API keys stay server-side

## Architecture
- **Frontend**: Streamlit app (`src/frontend/streamlit_app.py`) with custom styles (`src/frontend/styles.css`)
- **Backend**: FastAPI service (`src/backend/app.py`) handling prompt orchestration and parsing
- **Configs**: YAML-driven model/provider settings per side
  - Backend: `src/backend/config.yaml`
  - Frontend: `src/frontend/config.yaml`
- **Logging**: Structured JSONL in `src/backend/logs/easygpt.jsonl` (toggle via backend config)

## Requirements
- Python 3.10+
- Windows/macOS/Linux

## Quick start
1) Clone and open a terminal in the project root.

2) Create virtual envs (recommended per service):
```bash
# Backend
python -m venv .venv-backend
.venv-backend\Scripts\activate.bat # cmd on windows
# . .venv-backend/Scripts/Activate.ps1   # PowerShell on Windows
# source .venv-backend/bin/activate    # macOS/Linux
pip install -r src/backend/requirements.txt

# Frontend
python -m venv .venv-frontend
.venv-frontend\Scripts\activate.bat # cmd on windows
# . .venv-frontend/Scripts/Activate.ps1  # PowerShell on Windows
# source .venv-frontend/bin/activate   # macOS/Linux
pip install -r src/frontend/requirements.txt
```

3) Configure environment variables (create a `.env` in the project root or export in your shell):
```bash
# Backend (FastAPI)
EASYGPT_BACKEND_HOST=0.0.0.0
EASYGPT_BACKEND_PORT=8000
EASYGPT_FRONTEND_ORIGIN=http://localhost:8501
# LLM provider keys (optional if using mock)
OPENAI_API_KEY=...
GEMINI_API_KEY=...
DEEPSEEK_API_KEY=...

# Frontend (Streamlit)
EASYGPT_BACKEND_URL=http://localhost:8000
```
Both backend and frontend also read provider/model lists from their `config.yaml` files.

4) Run the backend:
```bash
# from project root
uvicorn src.backend.app:app --host 0.0.0.0 --port 8000 --reload
```

5) Run the frontend:
```bash
# from project root
streamlit run src/frontend/streamlit_app.py
```
Visit `http://localhost:8501`.

## Configuration
- Backend `src/backend/config.yaml` example:
```yaml
logging:
  enabled: true
  path: logs/easygpt.jsonl
models:
  default_provider: mock
  providers:
    mock: [mock-model]
    openai: [gpt-4o-mini]
    gemini: [gemini-1.5-pro]
    deepseek: [deepseek-chat]
```
- Frontend `src/frontend/config.yaml` example:
```yaml
models:
  default_provider: mock
  providers:
    mock: [mock-model]
```
On the frontend, the Model select is fixed to the first configured model for the chosen provider.

## How it works (brief)
- Frontend sends your prompt to `POST /v1/generate`
- Backend calls the chosen provider, returns parsed cards + usage
- You can step through cards, or view all
- Ask a follow-up on the current step via `POST /v1/followup`

## API
- `GET /health` → `{ "status": "ok" }`
- `POST /v1/generate`
  - body: `{ prompt, provider?, model?, temperature?, max_tokens? }`
  - returns: `{ cards: [...], usage: {...}, raw_text, meta }`
- `POST /v1/followup`
  - body: `{ current_card_title, current_card_content, question, provider?, model? }`
  - returns: `{ card, usage, raw_text }`

## Troubleshooting
- **Cannot connect to backend**: Ensure uvicorn is running and `EASYGPT_BACKEND_URL` matches (default `http://localhost:8000`).
- **API key errors**: Add provider keys to `.env` or select `mock` provider in the sidebar.

## Project layout
```
src/
  backend/
    app.py, config.py, config.yaml, schemas.py, services/, requirements.txt
  frontend/
    streamlit_app.py, frontend_service.py, config.yaml, styles.css, requirements.txt
```

## License
MIT (or your preferred license)