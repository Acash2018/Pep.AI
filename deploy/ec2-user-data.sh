#!/usr/bin/env bash
set -euxo pipefail

APP_DIR=/opt/pep-ai
REPO_URL=https://github.com/Acash2018/Pep.AI.git
OLLAMA_MODEL_NAME=llama3.2:3b
OLLAMA_EMBEDDING_MODEL_NAME=nomic-embed-text
POSTGRES_PASSWORD="$(openssl rand -hex 24)"

dnf update -y
dnf install -y docker git

systemctl enable --now docker

if [ ! -d "$APP_DIR/.git" ]; then
  git clone "$REPO_URL" "$APP_DIR"
fi

cd "$APP_DIR"
git pull --ff-only

cat > .env <<EOF
POSTGRES_DB=pep_ai
POSTGRES_USER=pep_user
POSTGRES_PASSWORD=$POSTGRES_PASSWORD

OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=$OLLAMA_MODEL_NAME
OLLAMA_EMBEDDING_MODEL=$OLLAMA_EMBEDDING_MODEL_NAME

NEXT_PUBLIC_API_BASE_URL=/api
EOF

docker compose -f docker-compose.prod.yml up --build -d

docker compose -f docker-compose.prod.yml exec -T ollama ollama pull "$OLLAMA_MODEL_NAME"
docker compose -f docker-compose.prod.yml exec -T ollama ollama pull "$OLLAMA_EMBEDDING_MODEL_NAME"

docker compose -f docker-compose.prod.yml ps
