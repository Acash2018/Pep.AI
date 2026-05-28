# Pep.AI

Pep.AI is a full-stack football scouting intelligence platform. It combines a Next.js dashboard, a FastAPI backend, LangGraph multi-agent analysis, ChromaDB retrieval, public football data ingestion, tactical metadata filtering, and persistent scouting memory.

The app is designed to answer questions such as:

- Which players fit a tactical system?
- Why does a player fit or not fit?
- Which players are similar by role, style, risk, and tactical suitability?
- How has a player's tactical profile evolved across saved reports?
- Which historical scouting reports and comparisons have already been generated?

## Core Features

- LangGraph multi-agent scouting workflow
- Stats Agent for production and statistical profile analysis
- Tactical Fit Agent for system fit, role suitability, and tactical reasoning
- Report Writer Agent for structured scouting report generation
- ChromaDB-backed football RAG system
- Structured football knowledge base
- StatsBomb Open Data ingestion
- Metadata-aware player retrieval
- Hard positional filtering before semantic ranking
- Tactical role and formation compatibility metadata
- Persistent player memory with SQLAlchemy
- PostgreSQL support with SQLite fallback
- Cached scouting reports to reduce repeated generation
- Historical player timeline
- Comparison history and matrix-based comparison intelligence
- Frontend pages for saved reports, comparisons, history, and player profiles

## Tech Stack

### Frontend

- Next.js 14
- React 18
- TypeScript
- TailwindCSS

### Backend

- FastAPI
- LangGraph
- ChromaDB
- SQLAlchemy
- PostgreSQL via `psycopg`
- SQLite local fallback
- StatsBomb Open Data ingestion

## Project Structure

```text
Pep.AI/
  backend/
    app/
      api/
        routes.py
      data/
        mock_players.py
        dynamic_players.py
        player_repository.py
      db/
        models.py
        session.py
      knowledge_base/
        player_profiles/
        player_roles/
        scouting_reports/
        tactical_analysis/
        tactical_systems/
      services/
        agents.py
        embeddings.py
        football_metadata.py
        intelligence_metrics.py
        knowledge_base.py
        metadata_retrieval.py
        persistence.py
        player_comparison.py
        players.py
        prompts.py
        role_matching.py
        state.py
        statsbomb.py
        tactical_scoring.py
        vector_search.py
        workflow.py
      utils/
        chromadb_client.py
      main.py
      models.py
    requirements.txt
    .env.example
  frontend/
    app/
      page.tsx
      compare/page.tsx
      history/page.tsx
      reports/page.tsx
      players/[id]/page.tsx
    components/
    types/
    package.json
```

## Quick Start

### 1. Backend

From the project root:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The backend runs at:

```text
http://127.0.0.1:8000
```

FastAPI docs:

```text
http://127.0.0.1:8000/docs
```

### 2. Frontend

Open another terminal:

```powershell
cd frontend
npm install
npm run dev
```

The frontend runs at:

```text
http://localhost:3000
```

## Environment Variables

Copy the backend environment example:

```powershell
cd backend
Copy-Item .env.example .env
```

Example values:

```env
OPENAI_API_KEY=your-openai-api-key
CHROMA_PERSIST_DIR=./chromadb
DATABASE_URL=postgresql+psycopg://pep_user:pep_password@localhost:5432/pep_ai
LANGGRAPH_API_KEY=your-langgraph-api-key
API_PORT=8000
```

### Database Behavior

Pep.AI supports PostgreSQL, but defaults to local SQLite if `DATABASE_URL` is not set.

Default fallback:

```text
sqlite:///./pep_ai.db
```

PostgreSQL example:

```env
DATABASE_URL=postgresql+psycopg://pep_user:pep_password@localhost:5432/pep_ai
```

The database tables are created automatically on FastAPI startup.

## LangGraph Multi-Agent Workflow

The scouting pipeline lives in:

```text
backend/app/services/workflow.py
```

Workflow:

```text
load_player
  -> stats_agent
  -> tactical_fit_agent
  -> report_writer_agent
```

### Stats Agent

Analyzes:

- goals
- assists
- pass accuracy
- statistical strengths
- statistical weaknesses
- production signals

### Tactical Fit Agent

Analyzes:

- requested tactical system
- identified system archetype
- player role suitability
- tactical strengths
- tactical weaknesses
- why the player fits
- why the player may not fit
- retrieved tactical and role knowledge
- system compatibility score from `0-100`

### Report Writer Agent

Generates:

- executive scouting summary
- final recommendation
- tactical reasoning
- role suitability
- system compatibility
- transfer value
- similar players
- retrieved football knowledge references

## Football Knowledge Base

The knowledge base is stored in:

```text
backend/app/knowledge_base/
```

Included categories:

```text
scouting_reports/
tactical_analysis/
tactical_systems/
player_roles/
player_profiles/
```

### Tactical Systems

```text
tactical_systems/angeball.md
tactical_systems/pep_positional_play.md
tactical_systems/low_block_counter.md
tactical_systems/gegenpressing.md
```

### Player Roles

```text
player_roles/inverted_winger.md
player_roles/ball_progressor.md
player_roles/deep_lying_playmaker.md
player_roles/pressing_forward.md
```

## RAG System

Pep.AI uses ChromaDB for vector retrieval.

Main services:

```text
backend/app/services/embeddings.py
backend/app/services/vector_search.py
backend/app/services/knowledge_base.py
backend/app/utils/chromadb_client.py
```

The embeddings service currently uses deterministic local embeddings, so the RAG pipeline works without an external embedding API.

### Ingest Knowledge Base

```http
POST /api/knowledge/ingest
```

Example:

```powershell
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/knowledge/ingest"
```

### Search Knowledge Base

```http
GET /api/knowledge/search?q=wide build up wing back
```

Example:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/knowledge/search?q=gegenpressing"
```

## Metadata-Aware Retrieval

Pep.AI includes a structured football metadata layer to avoid bad semantic matches.

Problem solved:

```text
"ball-playing center back in a back 3"
```

Previously, this could retrieve attacking midfielders because terms like "progression" and "passing" overlapped semantically.

Now retrieval applies:

1. structured metadata extraction
2. hard positional filtering
3. role and formation filtering
4. semantic ranking
5. tactical relevance reranking

Main files:

```text
backend/app/services/football_metadata.py
backend/app/services/metadata_retrieval.py
```

### Metadata Fields

Players are enriched with:

```text
primary_position
secondary_positions
position_family
tactical_roles
suitable_formations
defensive_line_type
progression_profile
pressing_profile
tactical_archetype
```

### Retrieval Scores

Search results can include:

```text
positional_confidence_score
tactical_relevance_score
role_overlap_score
formation_compatibility_score
lexical_score
weighted_score
```

### Example Query

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/players/search?q=ball-playing%20center%20back%20in%20a%20back%203"
```

Expected top results after StatsBomb ingestion:

```text
Josip Stanisic - Right Center Back - Ball-playing defender
Jonathan Tah - Center Back - Ball-playing defender
Diogo Leite - Left Center Back - Ball-playing defender
Odilon Kossonou - Right Center Back - Ball-playing defender
Edmond Tapsoba - Left Center Back - Ball-playing defender
```

## Dynamic Player Ingestion

Pep.AI can ingest public StatsBomb Open Data.

Endpoint:

```http
POST /api/players/ingest/statsbomb?max_matches=6
```

Example:

```powershell
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/players/ingest/statsbomb?max_matches=6"
```

This fetches match, lineup, and event data, then transforms players into Pep.AI scouting profiles.

Generated player fields include:

- position
- club
- nationality
- goals
- assists
- pass accuracy
- inferred strengths
- inferred weaknesses
- tactical style
- estimated value
- tactical metadata

## Persistence Layer

Pep.AI persists scouting intelligence using SQLAlchemy.

Main files:

```text
backend/app/db/models.py
backend/app/db/session.py
backend/app/services/persistence.py
```

### Database Entities

```text
Player
ScoutingReport
TacticalProfile
Comparison
KnowledgeSource
PlayerSearchHistory
```

### Persisted Intelligence

Pep.AI saves:

- analyzed players
- generated scouting reports
- tactical profiles
- tactical fit evolution
- player search history
- comparison history
- knowledge source metadata

### Cached Reports

Repeated scouting requests with the same:

```text
player_id
club
preferred_system
cache version
```

return the saved report instead of regenerating the full workflow.

Cached responses include:

```json
{
  "cached": true
}
```

## Intelligence Scores

Scouting reports include:

```text
consistency_score
risk_profile_score
scouting_confidence_score
development_trajectory_notes
```

These are generated in:

```text
backend/app/services/intelligence_metrics.py
```

## Player Comparison Engine

The comparison engine lives in:

```text
backend/app/services/player_comparison.py
```

It compares players by:

- primary position
- position family
- role adjacency
- shared strengths
- shared weaknesses
- pass accuracy gap
- attacking output gap
- age gap
- tactical style overlap
- tactical suitability
- risk delta
- metadata relevance

Comparison output includes:

```text
similarityScore
similarityReasons
attributeSimilarity
tacticalSimilarityScore
riskDelta
stylisticOverlap
strengthWeaknessMatrix
comparisonMatrix
```

## API Reference

### Player Routes

```http
GET /api/players
GET /api/players/search?q=...
GET /api/players/{player_id}
POST /api/players/ingest/statsbomb?max_matches=6
```

### Scouting Routes

```http
POST /api/scout-player
POST /api/reports
```

Example request:

```json
{
  "player_id": "p1",
  "club": "Pep.AI XI",
  "preferred_system": "High press & quick transitions"
}
```

Example response shape:

```json
{
  "player": {},
  "strengths": [],
  "weaknesses": [],
  "tactical_fit": {
    "fit_score": 89,
    "fit_grade": "Elite fit",
    "identified_system": "Gegenpressing",
    "role_match": {},
    "system_compatibility": {},
    "tactical_strengths": [],
    "tactical_weaknesses": [],
    "why_fit": [],
    "why_not": [],
    "retrieved_knowledge": []
  },
  "transfer_value": "EUR 52m",
  "similar_players": [],
  "report": {},
  "memory": {
    "risk_profile_score": 57,
    "consistency_score": 80,
    "scouting_confidence_score": 85,
    "development_trajectory_notes": "..."
  }
}
```

### Knowledge Routes

```http
POST /api/knowledge/ingest
GET /api/knowledge/search?q=...
```

### Memory Routes

```http
GET /api/memory/reports
GET /api/memory/players
GET /api/memory/players/{player_id}/timeline
GET /api/memory/comparisons/{player_id}
```

## Frontend Pages

### Dashboard

```text
/
```

Features:

- search players
- ingest StatsBomb data
- scout selected player
- view tactical fit
- view role suitability
- view retrieved football knowledge
- view memory metrics
- view similar players

### Saved Reports

```text
/reports
```

Shows cached scouting reports with:

- player
- requested system
- fit score
- risk score
- confidence score
- development notes

### Comparison Dashboard

```text
/compare
```

Shows saved player comparisons with:

- similarity score
- tactical score
- risk delta
- strengths matrix
- weaknesses matrix

### Historical Analysis

```text
/history
```

Shows:

- player timeline
- saved reports
- tactical fit evolution

### Player Profile

```text
/players/{id}
```

Shows:

- player profile
- report count
- latest tactical fit
- latest risk score
- development timeline

## Suggested Demo Flow

1. Start backend and frontend.
2. Open:

```text
http://localhost:3000
```

3. Click:

```text
Ingest public data
```

4. Search:

```text
ball-playing center back in a back 3
```

5. Confirm results are center backs, not attacking midfielders.
6. Select a player such as:

```text
Jonathan Tah
```

7. Try systems:

```text
Gegenpressing
Pep positional play
Low block counter
Angeball
```

8. Open:

```text
/reports
/compare
/history
```

## Useful Test Commands

### Backend Compile Check

```powershell
cd backend
python -m compileall app
```

### Frontend Type Check

```powershell
cd frontend
npx tsc --noEmit
```

### Scout Player Through API

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/scout-player" `
  -ContentType "application/json" `
  -Body '{"player_id":"p1","club":"Pep.AI XI","preferred_system":"High press & quick transitions"}'
```

### Verify Metadata Search

```powershell
Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/api/players/search?q=ball-playing%20center%20back%20in%20a%20back%203"
```

### List Saved Reports

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/memory/reports"
```

### Player Timeline

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/memory/players/p1/timeline"
```

## Known Development Notes

- StatsBomb ingested players are stored in memory for the running backend session.
- Generated scouting reports and player memory are persisted in the SQL database.
- ChromaDB persists vector data under `CHROMA_PERSIST_DIR`.
- The local embedding service is deterministic and API-free.
- OpenAI is included as a dependency but current deterministic workflows do not require an API key.
- If Next.js cache errors occur on Windows/OneDrive, stop Node processes and delete `frontend/.next`.

## Troubleshooting

### Port 3000 Is In Use

Next.js may fall back to `3001`. Stop stale Node processes or run:

```powershell
netstat -ano | Select-String ':3000'
```

Then stop the process ID if needed.

### ChromaDB Issues

Make sure dependencies are installed:

```powershell
cd backend
pip install -r requirements.txt
```

Then re-ingest:

```powershell
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/knowledge/ingest"
```

### No Saved Reports

Generate at least one report:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/scout-player" `
  -ContentType "application/json" `
  -Body '{"player_id":"p1","club":"Pep.AI XI","preferred_system":"Pep positional play"}'
```

Then open:

```text
http://localhost:3000/reports
```

## License And Data

Pep.AI currently uses mock player profiles and public StatsBomb Open Data for demo ingestion. Check StatsBomb's open-data license and terms before using that data outside development or demo contexts.
