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
- Ollama local LLM reasoning
- ChromaDB
- SQLAlchemy
- PostgreSQL via `psycopg`
- SQLite local fallback
- StatsBomb Open Data ingestion

## Design Diagram

This is the full application flow from the dashboard through the backend, retrieval layer, agent workflow, persistence layer, and final scouting output.

```mermaid
flowchart TB
    User["User / Scout"]
    Browser["Next.js Frontend Dashboard"]

    User --> Browser

    Browser -->|Search players| API["FastAPI Backend"]
    Browser -->|Scout player| API
    Browser -->|Ingest public data| API
    Browser -->|View reports/history/compare| API

    subgraph Frontend["Frontend"]
        Browser
        Pages["Dashboard / Reports / History / Compare / Player Profile"]
        Browser --> Pages
    end

    subgraph Backend["Backend - FastAPI"]
        API --> Routes["API Routes"]
        Routes --> PlayerService["Player Service"]
        Routes --> IngestService["StatsBomb Ingestion Service"]
        Routes --> Workflow["LangGraph Scouting Workflow"]
        Routes --> MemoryService["Persistence / Memory Services"]
        Routes --> KnowledgeService["Knowledge Base Service"]
    end

    subgraph DataIngestion["Public Data Ingestion"]
        StatsBomb["StatsBomb Open Data GitHub"]
        IngestService -->|Fetch matches, lineups, events| StatsBomb
        IngestService -->|Aggregate event data| ProfileBuilder["Player Profile Builder"]
        ProfileBuilder --> MetadataEnrichment["Football Metadata Enrichment"]
    end

    subgraph Intelligence["Football Intelligence Layer"]
        KnowledgeFolder["Football Knowledge Base Folder"]
        TacticalDocs["Tactical Systems Docs"]
        RoleDocs["Player Role Docs"]
        ScoutDocs["Scouting Reports"]
        AnalysisDocs["Tactical Analysis Files"]

        KnowledgeFolder --> TacticalDocs
        KnowledgeFolder --> RoleDocs
        KnowledgeFolder --> ScoutDocs
        KnowledgeFolder --> AnalysisDocs

        KnowledgeService --> Embeddings["Embeddings Service"]
        Embeddings --> Chroma["ChromaDB Vector Store"]
        KnowledgeService --> VectorSearch["Metadata-Aware Vector Search"]
        VectorSearch --> Chroma
    end

    subgraph WorkflowLayer["LangGraph Multi-Agent Workflow"]
        Workflow --> StatsAgent["Stats Agent"]
        StatsAgent --> TacticalFitAgent["Tactical Fit Agent"]
        TacticalFitAgent --> ReportWriter["Report Writer Agent"]

        TacticalFitAgent --> TacticalScoring["Tactical Fit Scoring"]
        TacticalFitAgent --> RoleMatching["Role Matching Service"]
        TacticalFitAgent --> ComparisonEngine["Player Comparison Engine"]
        TacticalFitAgent --> VectorSearch
    end

    subgraph Reasoning["LLM Reasoning Layer"]
        Ollama["Ollama - llama3.2:3b"]
        TacticalFitAgent -->|Tactical reasoning| Ollama
        ReportWriter -->|Final report generation| Ollama
        ComparisonEngine -->|Comparison explanation| Ollama
    end

    subgraph Persistence["Persistent Memory Layer"]
        Postgres["PostgreSQL / RDS"]
        PlayerTable["Player"]
        ReportTable["ScoutingReport"]
        TacticalTable["TacticalProfile"]
        ComparisonTable["Comparison"]
        KnowledgeTable["KnowledgeSource"]
        SearchTable["SearchHistory"]

        MemoryService --> Postgres
        MetadataEnrichment --> Postgres
        Workflow --> MemoryService

        Postgres --> PlayerTable
        Postgres --> ReportTable
        Postgres --> TacticalTable
        Postgres --> ComparisonTable
        Postgres --> KnowledgeTable
        Postgres --> SearchTable
    end

    subgraph Output["Scouting Output"]
        FinalReport["Professional Scouting Report"]
        Strengths["Strengths"]
        Weaknesses["Weaknesses"]
        TacticalFit["Tactical Fit"]
        TransferValue["Transfer Value"]
        SimilarPlayers["Similar Players"]
        Risks["Recruitment Risks"]
        Recommendation["Final Recommendation"]

        ReportWriter --> FinalReport
        FinalReport --> Strengths
        FinalReport --> Weaknesses
        FinalReport --> TacticalFit
        FinalReport --> TransferValue
        FinalReport --> SimilarPlayers
        FinalReport --> Risks
        FinalReport --> Recommendation
    end

    API --> FinalReport
    FinalReport --> Browser
```

## AWS Deployment Diagram

The AWS deployment uses ECS/Fargate, RDS, EFS, ALB, WAF, ECR, CloudWatch, Secrets Manager, ChromaDB persistence, and an Ollama sidecar for local model reasoning.

```mermaid
flowchart TB
    User["User Browser"]
    WAF["AWS WAF<br/>IP allowlist + rate limiting"]
    ALB["Application Load Balancer"]

    User --> WAF
    WAF --> ALB

    ALB -->|/| FrontendSvc["ECS Fargate Frontend Service<br/>Next.js"]
    ALB -->|/api/*| BackendSvc["ECS Fargate Backend Service<br/>FastAPI"]

    subgraph ECS["Amazon ECS / Fargate"]
        FrontendSvc

        subgraph BackendTask["Backend Task"]
            BackendContainer["FastAPI Container"]
            OllamaContainer["Ollama Sidecar<br/>llama3.2:3b"]
            BackendContainer -->|localhost:11434| OllamaContainer
        end

        BackendSvc --> BackendTask
    end

    BackendContainer --> RDS["Amazon RDS PostgreSQL<br/>Player memory, reports, comparisons"]
    BackendContainer --> EFS["Amazon EFS<br/>ChromaDB + Ollama model files"]
    BackendContainer --> Chroma["ChromaDB<br/>Vector search"]
    Chroma --> EFS

    BackendContainer --> StatsBomb["StatsBomb Open Data<br/>GitHub JSON"]
    BackendContainer --> CloudWatch["CloudWatch Logs"]

    FrontendSvc --> CloudWatch

    ECR["Amazon ECR<br/>Docker images"]
    ECR --> FrontendSvc
    ECR --> BackendSvc

    Secrets["AWS Secrets Manager<br/>DATABASE_URL"]
    Secrets --> BackendContainer
```

Short architecture summary:

```text
User
-> Next.js dashboard
-> FastAPI backend
-> LangGraph scouting workflow
-> Stats Agent / Tactical Fit Agent / Report Writer Agent
-> ChromaDB football RAG + tactical metadata filtering
-> Ollama reasoning layer
-> PostgreSQL scouting memory
-> final scouting report back to frontend
```

## Core Backend Technologies

This section explains the main backend tools and how Pep.AI uses each one.

### FastAPI

FastAPI is the Python web framework that powers the backend HTTP API.

In Pep.AI, FastAPI is responsible for:

- exposing routes for the frontend
- receiving scouting requests
- returning player data, reports, timelines, and comparison results
- handling request validation through Pydantic models
- serving interactive API docs at `/docs`
- running startup logic such as database initialization

Main files:

```text
backend/app/main.py
backend/app/api/routes.py
backend/app/models.py
```

Example route:

```text
POST /api/scout-player
```

When the frontend clicks `Scout player`, it sends a request to FastAPI. FastAPI passes that request into the scouting services, then returns the structured report JSON back to the dashboard.

### LangGraph

LangGraph is the workflow orchestration library used to model Pep.AI's scouting process as a graph of agents.

In Pep.AI, LangGraph connects the scouting agents in a predictable sequence:

```text
load_player
  -> stats_agent
  -> tactical_fit_agent
  -> report_writer_agent
```

Main file:

```text
backend/app/services/workflow.py
```

Pep.AI uses LangGraph to:

- maintain shared scouting state between agents
- run the Stats Agent, Tactical Fit Agent, and Report Writer Agent in order
- pass player data, retrieved knowledge, tactical scores, and report sections between steps
- keep the scouting workflow modular and easier to extend

The shared graph state is defined in:

```text
backend/app/services/state.py
```

The current workflow is deterministic and service-driven, but the structure is ready for deeper LLM-backed agent reasoning later.

### Ollama

Ollama is used as the local LLM runtime for Pep.AI's reasoning and report-writing layer.

Important: Ollama does not replace Pep.AI's retrieval, metadata filtering, tactical scoring, role matching, or comparison logic. Those systems still run first and produce the factual evidence. The local Ollama model receives that assembled context and explains it in professional scouting language.

Main file:

```text
backend/app/services/ollama_service.py
```

Prompt definitions:

```text
backend/app/services/prompts.py
```

The Ollama reasoning layer is used for:

- Scout Agent reasoning: strengths, weaknesses, development areas
- Tactical Fit Agent reasoning: tactical suitability, tactical risks, formation fit
- Comparison Agent reasoning: stylistic similarities and differences
- Report Writer Agent output: final professional scouting report

The local LLM receives:

- player profile
- tactical metadata
- tactical role
- formation suitability
- deterministic fit score
- tactical strengths
- tactical weaknesses
- retrieved ChromaDB football knowledge
- comparison candidates

Environment variables:

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1
```

If Ollama is not running, Pep.AI uses deterministic fallback text and the app continues working locally.

### ChromaDB

ChromaDB is the vector database used for Pep.AI's football knowledge retrieval system.

In Pep.AI, ChromaDB stores embedded chunks of football knowledge from markdown documents inside:

```text
backend/app/knowledge_base/
```

Those documents include:

- tactical systems
- player role archetypes
- scouting reports
- tactical analysis
- player profile archetypes

Main files:

```text
backend/app/utils/chromadb_client.py
backend/app/services/embeddings.py
backend/app/services/vector_search.py
backend/app/services/knowledge_base.py
```

Pep.AI uses ChromaDB to:

- store vector embeddings of football knowledge documents
- retrieve relevant tactical and role context during scouting
- support RAG for the Tactical Fit Agent
- ground tactical explanations in indexed football intelligence

Example:

When the user scouts a player for:

```text
Gegenpressing
```

the Tactical Fit Agent retrieves relevant knowledge such as:

```text
tactical_systems/gegenpressing.md
player_roles/pressing_forward.md
```

Then the agent summarizes that context into scouting language, for example:

```text
Retrieved football intelligence emphasizes immediate counter-pressing after turnovers,
compact team spacing, and vertical progression.
```

ChromaDB persistence is controlled by:

```env
CHROMA_PERSIST_DIR=./chromadb
```

### SQLAlchemy

SQLAlchemy is the database toolkit and ORM (Object-Relational Mapping). used for Pep.AI's persistent memory layer.

In Pep.AI, SQLAlchemy maps Python classes to database tables and lets the backend save and retrieve scouting intelligence.

Main files:

```text
backend/app/db/models.py
backend/app/db/session.py
backend/app/services/persistence.py
```

Pep.AI uses SQLAlchemy to persist:

- players
- generated scouting reports
- tactical profiles
- comparison history
- knowledge source records
- player search history

Database entities include:

```text
Player
ScoutingReport
TacticalProfile
Comparison
KnowledgeSource
PlayerSearchHistory
```

SQLAlchemy also powers the scouting report cache. When the same player/system request is made again, Pep.AI checks the database first. If a cached report exists, it returns that saved report instead of rerunning the whole LangGraph workflow.

Database configuration:

```env
DATABASE_URL=postgresql+psycopg://pep_user:pep_password@localhost:5432/pep_ai
```

If `DATABASE_URL` is not set, Pep.AI falls back to local SQLite:

```text
sqlite:///./pep_ai.db
```

This means local development works immediately, while production can use PostgreSQL.

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

## Docker Quick Start

Pep.AI can run as a Docker Compose stack with:

- Caddy reverse proxy
- Next.js frontend
- FastAPI backend
- PostgreSQL database
- persistent ChromaDB volume
- Ollama local LLM runtime

### 1. Copy Docker Environment

From the project root:

```powershell
Copy-Item .env.docker.example .env
```

Edit `.env`:

```env
POSTGRES_DB=pep_ai
POSTGRES_USER=pep_user
POSTGRES_PASSWORD=change-this-password

OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama3.1
OLLAMA_EMBEDDING_MODEL=nomic-embed-text

NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api
```

For local development, Pep.AI will use deterministic fallback reasoning if Ollama is not running or the configured model has not been pulled.

### 2. Build And Run

```powershell
docker compose up --build
```

Services:

```text
Frontend: http://localhost:3000
Backend:  http://localhost:8000
Postgres: localhost:5432
Ollama:   localhost:11434
```

### 3. Stop The Stack

```powershell
docker compose down
```

### 4. Stop And Delete Volumes

Use this only when you want to erase local database and Chroma data:

```powershell
docker compose down -v
```

### Docker Files

```text
backend/Dockerfile
frontend/Dockerfile
docker-compose.yml
docker-compose.prod.yml
.env.docker.example
.dockerignore
```

### Production Compose

For a single server such as EC2 or Lightsail, use:

```powershell
docker compose -f docker-compose.prod.yml up --build -d
```

Set production values in `.env`:

```env
POSTGRES_PASSWORD=strong-production-password
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama3.2:3b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
NEXT_PUBLIC_API_BASE_URL=/api
```

Production Compose includes Caddy, so public traffic can use one origin:

```text
http://your-server-ip
  -> Caddy
  -> /api/* to FastAPI backend
  -> everything else to Next.js frontend
```

Only port `80` needs to be open publicly. Do not expose `3000`, `8000`, `5432`, or `11434` to the internet.

### EC2 Demo Runbook

Use this when restarting the EC2 instance for future demos.

SSH into the instance:

```powershell
ssh -i "$env:USERPROFILE\Downloads\pep-ai-key.pem" ec2-user@YOUR_EC2_PUBLIC_IP
```

Go to the app directory:

```bash
cd /opt/pep-ai
```

If Docker Compose is missing and `docker compose` shows `unknown shorthand flag: 'f' in -f`, install the Compose plugin manually:

```bash
sudo mkdir -p /usr/local/lib/docker/cli-plugins

sudo curl -SL https://github.com/docker/compose/releases/download/v2.29.7/docker-compose-linux-x86_64 \
  -o /usr/local/lib/docker/cli-plugins/docker-compose

sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

sudo mkdir -p /usr/libexec/docker/cli-plugins
sudo ln -sf /usr/local/lib/docker/cli-plugins/docker-compose /usr/libexec/docker/cli-plugins/docker-compose

sudo docker compose version
```

Create or refresh the production `.env` file:

```bash
POSTGRES_PASSWORD="$(openssl rand -hex 24)"

sudo tee .env >/dev/null <<EOF
POSTGRES_DB=pep_ai
POSTGRES_USER=pep_user
POSTGRES_PASSWORD=$POSTGRES_PASSWORD

OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama3.2:3b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text

NEXT_PUBLIC_API_BASE_URL=/api
EOF
```

Start the full production stack:

```bash
sudo systemctl enable --now docker
sudo git pull --ff-only
sudo docker compose -f docker-compose.prod.yml up --build -d
```

Pull the Ollama models:

```bash
sudo docker compose -f docker-compose.prod.yml exec -T ollama ollama pull llama3.2:3b
sudo docker compose -f docker-compose.prod.yml exec -T ollama ollama pull nomic-embed-text
```

Check container status:

```bash
sudo docker compose -f docker-compose.prod.yml ps
```

Check logs:

```bash
sudo docker compose -f docker-compose.prod.yml logs --tail=120
```

Test the backend through Caddy:

```bash
curl http://localhost/api/health
```

Open the app:

```text
http://YOUR_EC2_PUBLIC_IP
```

Stop the app after a demo:

```bash
cd /opt/pep-ai
sudo docker compose -f docker-compose.prod.yml down
```

If Compose is still unavailable but containers are running, stop all running containers:

```bash
sudo docker ps
sudo docker stop $(sudo docker ps -q)
```

To reduce AWS cost, stop the EC2 instance from the AWS Console after the demo.

### ECS/Fargate + RDS + ALB Deployment

Pep.AI also includes a production-style AWS deployment scaffold under:

```text
infra/terraform/
deploy/ecs/push-images.ps1
```

This deployment uses:

- Amazon ECS on Fargate for the frontend and backend containers
- Amazon ECR for Docker image repositories
- Application Load Balancer for public HTTP traffic
- Path-based ALB routing:
  - `/api/*` -> FastAPI backend
  - everything else -> Next.js frontend
- Amazon RDS PostgreSQL for persistent scouting memory
- Amazon EFS mounted into the backend for ChromaDB persistence
- AWS Secrets Manager for `DATABASE_URL`
- CloudWatch Logs for container logs

High-level architecture:

```text
Browser
  -> Application Load Balancer
      -> /api/* to backend ECS service
      -> /* to frontend ECS service

Backend ECS service
  -> RDS PostgreSQL
  -> EFS /app/chromadb
  -> Ollama endpoint if configured
```

First create the ECR repositories:

```powershell
cd infra/terraform
Copy-Item terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars and set db_password.
terraform init
terraform apply `
  -target=aws_ecr_repository.frontend `
  -target=aws_ecr_repository.backend
```

Build and push images:

```powershell
cd ..\..
.\deploy\ecs\push-images.ps1 -Region us-east-1
```

Deploy the full AWS stack:

```powershell
cd infra/terraform
terraform apply
```

Get the public ALB URL:

```powershell
terraform output alb_dns_name
```

Destroy the stack when finished to avoid ongoing costs:

```powershell
terraform destroy
```

This ECS/Fargate deployment is more production-like than the EC2 Docker Compose demo, but it is also more expensive. Use it when you want the stronger AWS architecture story.

### Docker Persistence

Docker Compose creates named volumes:

```text
caddy_data
caddy_config
postgres_data
chroma_data
ollama_data
```

These store:

- persisted players
- saved scouting reports
- tactical profile history
- comparison history
- ChromaDB vector data
- Ollama model files
- Caddy runtime data

As long as you do not run `docker compose down -v`, this data survives container restarts.

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
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1
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

- StatsBomb ingested players are persisted in the SQL database.
- Generated scouting reports and player memory are persisted in the SQL database.
- ChromaDB persists vector data under `CHROMA_PERSIST_DIR`.
- The embedding service uses Ollama embeddings when available and deterministic fallback vectors when Ollama is offline.
- Ollama is used for local LLM reasoning when available; deterministic fallback text is used when Ollama is offline.
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
