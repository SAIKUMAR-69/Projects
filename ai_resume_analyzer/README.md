# AI-Powered Resume Analyzer

Flask web app that analyzes resumes and generates tailored job-fit recommendations using Pandas + SQL + OpenAI.

## Features
- Upload PDF/DOCX/TXT resumes
- Keyword overlap scoring (fast heuristic)
- LLM-powered summary + improvement tips
- SQLite via SQLAlchemy
- Responsive HTML/CSS/JS UI
- Seed sample jobs; view recent evaluations

## Quickstart (Local)
```bash
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# add your API key
cp .env.example .env
# edit .env and set OPENAI_API_KEY=sk-...

# init db and seed
python scripts/init_db.py
python scripts/seed_jobs.py

# run
flask --app app run --debug
# open http://127.0.0.1:5000
```

## Docker
```bash
docker compose up --build
```

## Environment Variables
- `OPENAI_API_KEY` (required for LLM features)
- `OPENAI_MODEL` (optional, default `gpt-4o-mini`)
- `FLASK_SECRET_KEY` (optional)
- `DATABASE_URL` (optional, default sqlite in ./instance)

## Notes
- If `OPENAI_API_KEY` is not set, the app still runs with heuristic output.
- Max upload size is 10 MB. Supported: PDF, DOCX, TXT.
- This project is intentionally simple—extend with authentication, role-based access, and better scoring as needed.
