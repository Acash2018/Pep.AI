#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

echo "Pep.AI Docker startup"
echo "Working directory: $ROOT_DIR"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is not installed or not available on PATH."
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "Docker is installed, but the Docker daemon is not running."
  echo "Start Docker Desktop or your Docker service, then rerun this script."
  exit 1
fi

if [ ! -f ".env" ]; then
  echo "No .env found. Creating one from .env.docker.example..."
  cp .env.docker.example .env
  echo "Created .env. Edit it later to change Ollama models if needed."
fi

echo "Building and starting Pep.AI..."
docker compose up --build -d

OLLAMA_MODEL_NAME="$(grep -E '^OLLAMA_MODEL=' .env | cut -d '=' -f2- || true)"
OLLAMA_MODEL_NAME="${OLLAMA_MODEL_NAME:-llama3.1}"
OLLAMA_EMBEDDING_MODEL_NAME="$(grep -E '^OLLAMA_EMBEDDING_MODEL=' .env | cut -d '=' -f2- || true)"
OLLAMA_EMBEDDING_MODEL_NAME="${OLLAMA_EMBEDDING_MODEL_NAME:-nomic-embed-text}"

echo "Ensuring Ollama model is available: $OLLAMA_MODEL_NAME"
docker compose exec -T ollama ollama pull "$OLLAMA_MODEL_NAME" || {
  echo "Could not pull $OLLAMA_MODEL_NAME automatically."
  echo "You can retry with: docker compose exec ollama ollama pull $OLLAMA_MODEL_NAME"
}

echo "Ensuring Ollama embedding model is available: $OLLAMA_EMBEDDING_MODEL_NAME"
docker compose exec -T ollama ollama pull "$OLLAMA_EMBEDDING_MODEL_NAME" || {
  echo "Could not pull $OLLAMA_EMBEDDING_MODEL_NAME automatically."
  echo "You can retry with: docker compose exec ollama ollama pull $OLLAMA_EMBEDDING_MODEL_NAME"
}

echo
echo "Pep.AI is starting."
echo "Frontend: http://localhost:3000"
echo "Backend:  http://localhost:8000"
echo "API docs: http://localhost:8000/docs"
echo
echo "Useful commands:"
echo "  docker compose logs -f"
echo "  docker compose ps"
echo "  docker compose exec ollama ollama pull $OLLAMA_MODEL_NAME"
echo "  docker compose exec ollama ollama pull $OLLAMA_EMBEDDING_MODEL_NAME"
echo "  docker compose down"
echo "  docker compose down -v   # deletes Postgres and Chroma volumes"
