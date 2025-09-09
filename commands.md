cd "C:\side projects\EasyGPT"


# creating env
python -m venv .venv
pip install -r src/backend/requirements.txt
pip install -r src/frontend/requirements.txt


# activating env
.venv\Scripts\activate


# running the app
Backend : 
python -m uvicorn src.backend.main:app --host 0.0.0.0 --port 8000 --reload

frontend :
streamlit run src/frontend/app.py