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

## How The Backend Works

The backend is a FastAPI application that acts as the orchestration layer for scouting, retrieval, persistence, player search, public data ingestion, and historical intelligence.

At a high level, the backend does five jobs:

1. loads player data from mock profiles, public ingestion, and saved memory
2. enriches players with football-specific metadata
3. runs the LangGraph scouting workflow
4. retrieves tactical knowledge from ChromaDB
5. persists reports, tactical profiles, comparisons, and history

### Backend Entry Point

The FastAPI app starts in:

```text
backend/app/main.py
```

This file:

- creates the FastAPI app
- enables CORS for the Next.js frontend
- includes all API routes under `/api`
- initializes database tables on startup

Startup flow:

```text
FastAPI starts
  -> init_db()
  -> SQLAlchemy creates missing tables
  -> API routes become available
```

### API Layer

All HTTP routes are defined in:

```text
backend/app/api/routes.py
```

The API layer is intentionally thin. It receives requests, calls service modules, handles errors, and returns structured JSON.

Important route groups:

```text
/api/players/*
/api/scout-player
/api/knowledge/*
/api/memory/*
```

Example scouting request:

```text
POST /api/scout-player
```

Request body:

```json
{
  "player_id": "p1",
  "club": "Pep.AI XI",
  "preferred_system": "High press & quick transitions"
}
```

Backend flow:

```text
routes.py
  -> services/agents.py
  -> cache lookup
  -> LangGraph workflow if no cache
  -> persistence services
  -> JSON response
```

### Data Sources

Pep.AI currently uses three player-data sources.

#### 1. Mock Players

Stored in:

```text
backend/app/data/mock_players.py
```

These are stable demo profiles used when the app first starts.

#### 2. Dynamic StatsBomb Players

Stored in memory after ingestion:

```text
backend/app/data/dynamic_players.py
```

Ingestion service:

```text
backend/app/services/statsbomb.py
```

When the user clicks `Ingest public data`, the backend:

```text
fetches StatsBomb matches
  -> fetches lineups
  -> fetches events
  -> aggregates event stats by player
  -> infers strengths/weaknesses
  -> creates Pep.AI player profiles
  -> enriches profiles with metadata
  -> stores them in memory
```

#### 3. Persisted Historical Players

Stored in the SQL database as `Player` rows.

These are created when a player is scouted and saved through the persistence layer.

### Player Repository

Player lookup is centralized in:

```text
backend/app/data/player_repository.py
```

This combines mock players and dynamically ingested players, then enriches each profile with metadata.

Main functions:

```text
retrieve_all_player_data()
retrieve_player_data(player_id)
retrieve_similar_players(player)
```

### Football Metadata Enrichment

Metadata enrichment lives in:

```text
backend/app/services/football_metadata.py
```

This module turns plain football profile text into structured tactical metadata.

It infers:

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

Example:

```text
Position: Right Center Back
```

becomes:

```json
{
  "primary_position": "RCB",
  "secondary_positions": ["CB", "RB"],
  "position_family": "center_back",
  "tactical_roles": [
    "ball_playing_center_back",
    "defensive_progressor",
    "ball_progressor"
  ],
  "suitable_formations": ["back_3"],
  "progression_profile": "defensive_progression",
  "tactical_archetype": "Ball-playing defender"
}
```

This metadata is critical because it prevents bad retrieval results caused by vague semantic overlap.

### Metadata-Aware Player Search

Player search is handled by:

```text
backend/app/services/players.py
backend/app/services/metadata_retrieval.py
```

The search pipeline works like this:

```text
user query
  -> infer position constraints
  -> infer role constraints
  -> infer formation constraints
  -> hard-filter impossible positions
  -> score remaining players
  -> return weighted ranking
```

For example:

```text
ball-playing center back in a back 3
```

is parsed into constraints such as:

```text
positions: CB, LCB, RCB
roles: ball_playing_center_back
formations: back_3
```

That means attacking midfielders are removed before semantic ranking happens.

Ranking scores include:

```text
positional_confidence_score
tactical_relevance_score
role_overlap_score
formation_compatibility_score
lexical_score
weighted_score
```

### Scouting Orchestration

The scouting entry service is:

```text
backend/app/services/agents.py
```

Despite the name, this file is now mostly an orchestration wrapper. It:

1. checks whether a cached scouting report already exists
2. runs the LangGraph workflow if no cache exists
3. persists the generated scouting result
4. returns the final report payload

Pseudo-flow:

```text
scout_player(request)
  -> get_cached_scouting_result(request)
  -> if cached, return cached payload
  -> else run scouting_graph.invoke(...)
  -> persist_scouting_result(...)
  -> return persisted payload
```

### LangGraph Workflow

The multi-agent graph is defined in:

```text
backend/app/services/workflow.py
```

Workflow:

```text
load_player_node
  -> stats_agent_node
  -> tactical_fit_agent_node
  -> report_writer_agent_node
```

#### load_player_node

Responsibilities:

- retrieve the selected player
- compute similar players through the comparison engine
- attach estimated transfer value

#### stats_agent_node

Responsibilities:

- analyze goals, assists, pass accuracy
- add statistical strengths
- add statistical weaknesses
- create stat notes

#### tactical_fit_agent_node

Responsibilities:

- match the player to a role archetype
- retrieve tactical system context
- retrieve role archetype context
- retrieve general football knowledge
- score tactical fit from `0-100`
- explain why the player fits
- explain why the player may not fit
- return tactical strengths and weaknesses

This is where RAG and tactical intelligence combine.

#### report_writer_agent_node

Responsibilities:

- combine stats and tactical analysis
- generate executive scouting summary
- generate recommendation
- include role suitability
- include system compatibility
- include comparison and retrieved knowledge context

### Prompt Layer

Structured prompts live in:

```text
backend/app/services/prompts.py
```

The prompts define the responsibility boundaries for:

- Stats Agent
- Tactical Fit Agent
- Report Writer Agent

The current implementation is deterministic and service-driven, but the prompts make the workflow ready for LLM-backed generation.

### Tactical Intelligence Services

Several small services support the Tactical Fit Agent.

#### Role Matching

```text
backend/app/services/role_matching.py
```

Matches a player to archetypes such as:

```text
Ball Progressor
Deep-Lying Playmaker
Pressing Forward
Inverted Winger
```

#### Tactical Scoring

```text
backend/app/services/tactical_scoring.py
```

Scores fit from `0-100` based on:

- system archetype
- player strengths
- player weaknesses
- role match
- stats
- retrieved context
- tactical risk factors

#### Intelligence Metrics

```text
backend/app/services/intelligence_metrics.py
```

Generates:

```text
consistency_score
risk_profile_score
scouting_confidence_score
development_trajectory_notes
```

### RAG And ChromaDB

The RAG layer is split across:

```text
backend/app/services/embeddings.py
backend/app/services/vector_search.py
backend/app/services/knowledge_base.py
backend/app/utils/chromadb_client.py
```

Flow:

```text
knowledge_base/*.md files
  -> chunk documents
  -> create deterministic embeddings
  -> upsert into ChromaDB
  -> retrieve relevant chunks during tactical analysis
```

The Tactical Fit Agent retrieves:

```text
tactical system documents
role archetype documents
general scouting/tactical context
```

Then it summarizes the retrieved context as tactical concepts, for example:

```text
Retrieved football intelligence emphasizes immediate counter-pressing after turnovers,
compact team spacing, secure possession under pressure.
```

### Persistence Layer

Database setup:

```text
backend/app/db/session.py
```

Database models:

```text
backend/app/db/models.py
```

Persistence services:

```text
backend/app/services/persistence.py
```

The persistence layer saves:

- players
- scouting reports
- tactical profiles
- comparison history
- knowledge sources
- search history

### Scouting Report Cache

When a report is generated, Pep.AI creates a cache key from:

```text
cache version
player_id
club
preferred_system
```

If the same request is made again, the backend returns the saved report instead of rerunning the workflow.

This happens in:

```text
ScoutingReportPersistenceService.get_cached_report()
ScoutingReportPersistenceService.save_report()
```

### Player Memory

When a player is scouted, the backend persists:

```text
Player
ScoutingReport
TacticalProfile
Comparison rows
```

This creates a historical memory of:

- previous scouting reports
- previous tactical scores
- tactical fit evolution
- comparison history
- risk and confidence changes

### Historical Retrieval

Historical data is exposed through:

```text
GET /api/memory/reports
GET /api/memory/players
GET /api/memory/players/{player_id}/timeline
GET /api/memory/comparisons/{player_id}
```

The frontend uses these endpoints for:

```text
/reports
/history
/compare
/players/{id}
```

### Player Comparison Engine

The comparison engine is:

```text
backend/app/services/player_comparison.py
```

It compares players across:

- primary position
- secondary positions
- position family
- role adjacency
- shared strengths
- shared weaknesses
- pass accuracy gap
- output gap
- age gap
- tactical style overlap
- tactical suitability
- risk delta
- metadata relevance

It heavily penalizes unrelated positions and supports role-adjacent matches only when the metadata says they make football sense.

### Full Scouting Request Lifecycle

End-to-end flow for `POST /api/scout-player`:

```text
Frontend sends player_id + preferred_system
  -> FastAPI route receives request
  -> agents.py checks scouting report cache
  -> if cached, return saved payload
  -> if not cached:
      -> LangGraph loads player
      -> metadata enrichment provides football structure
      -> Stats Agent analyzes production
      -> Tactical Fit Agent retrieves RAG context
      -> Tactical Fit Agent scores system compatibility
      -> Report Writer Agent builds final report
      -> persistence service saves player memory
      -> persistence service saves scouting report
      -> persistence service saves tactical profile
      -> persistence service saves comparison history
      -> API returns structured scouting payload
```

The response then powers the dashboard, saved reports page, history page, comparison page, and player profile page.

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
