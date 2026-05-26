# Pep.AI

Pep.AI is a full-stack AI football scouting platform built as an MVP with:

- **Next.js** frontend
- **TailwindCSS** UI
- **TypeScript**
- **Python FastAPI** backend
- **ChromaDB** vector storage
- **OpenAI** integration
- **LangGraph** multi-agent orchestration

## Project structure

- `frontend/` - Next.js application and UI components
- `backend/` - FastAPI server, routes, mock data, and LangGraph workflow

## Quick start

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Backend
```bash
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Environment
Copy `.env.example` to `.env` in `backend/` and set the values.

## API
- `GET /api/players` - list players
- `GET /api/players/search?q=...` - search players
- `GET /api/players/{player_id}` - player details
- `POST /api/reports` - generate scouting report

## Notes
This MVP uses mock player data and a starter agent workflow. Expand the backend for real data ingestion and agent orchestration as needed.
