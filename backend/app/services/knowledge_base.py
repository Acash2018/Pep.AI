from pathlib import Path
from typing import Any
import hashlib

from sqlalchemy import select

from app.db.models import KnowledgeSource
from app.db.session import SessionLocal
from app.services.vector_search import VectorSearchService

KNOWLEDGE_BASE_DIR = Path(__file__).resolve().parents[1] / 'knowledge_base'
TEXT_EXTENSIONS = {'.md', '.txt'}


class KnowledgeBaseService:
    def __init__(self, vector_search_service: VectorSearchService | None = None):
        self.vector_search_service = vector_search_service or VectorSearchService()
        self._seeded = False

    def ingest_knowledge_base(self) -> dict[str, Any]:
        documents = []
        for path in sorted(KNOWLEDGE_BASE_DIR.rglob('*')):
            if not path.is_file() or path.suffix.lower() not in TEXT_EXTENSIONS:
                continue
            documents.extend(_document_chunks(path))

        count = self.vector_search_service.upsert_documents(documents)
        _persist_knowledge_sources()
        self._seeded = True
        return {
            'knowledge_base_dir': str(KNOWLEDGE_BASE_DIR),
            'documents_indexed': count,
        }

    def retrieve_for_tactical_fit(self, player: dict, preferred_system: str, limit: int = 4) -> list[dict[str, Any]]:
        query = (
            f"{player['position']} {player['tacticalStyle']} {preferred_system} "
            f"strengths {' '.join(player['strengths'])} weaknesses {' '.join(player['weaknesses'])}"
        )
        return self.retrieve(query=query, limit=limit)

    def retrieve_tactical_system_context(self, preferred_system: str, limit: int = 3) -> list[dict[str, Any]]:
        return self.retrieve(query=preferred_system, limit=limit, category='tactical_systems')

    def retrieve_role_context(self, role_archetype: str, player: dict, limit: int = 3) -> list[dict[str, Any]]:
        query = f"{role_archetype} {player['position']} {' '.join(player['strengths'])}"
        return self.retrieve(query=query, limit=limit, category='player_roles')

    def retrieve(self, query: str, limit: int = 5, category: str | None = None) -> list[dict[str, Any]]:
        try:
            if not self._seeded:
                self.ingest_knowledge_base()
            return self.vector_search_service.search(query=query, limit=limit, category=category)
        except RuntimeError:
            return []


def _document_chunks(path: Path, chunk_size: int = 900, overlap: int = 120) -> list[dict[str, Any]]:
    text = path.read_text(encoding='utf-8').strip()
    if not text:
        return []

    relative_path = path.relative_to(KNOWLEDGE_BASE_DIR)
    category = relative_path.parts[0] if len(relative_path.parts) > 1 else 'general'
    chunks = []
    start = 0
    chunk_index = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()
        if chunk:
            document_id = f"{relative_path.as_posix()}::{chunk_index}"
            chunks.append(
                {
                    'id': document_id,
                    'text': chunk,
                    'metadata': {
                        'source': relative_path.as_posix(),
                        'category': category,
                        'chunk_index': chunk_index,
                    },
                }
            )
        if end == len(text):
            break
        start = max(0, end - overlap)
        chunk_index += 1

    return chunks


def _persist_knowledge_sources() -> None:
    with SessionLocal() as db:
        for path in sorted(KNOWLEDGE_BASE_DIR.rglob('*')):
            if not path.is_file() or path.suffix.lower() not in TEXT_EXTENSIONS:
                continue

            text = path.read_text(encoding='utf-8').strip()
            relative_path = path.relative_to(KNOWLEDGE_BASE_DIR).as_posix()
            category = relative_path.split('/')[0] if '/' in relative_path else 'general'
            source = db.scalar(select(KnowledgeSource).where(KnowledgeSource.source_id == relative_path))
            if not source:
                source = KnowledgeSource(source_id=relative_path)
                db.add(source)

            source.category = category
            source.title = path.stem.replace('_', ' ').title()
            source.content_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()
            source.metadata_json = {'path': relative_path, 'characters': len(text)}
        db.commit()


knowledge_base_service = KnowledgeBaseService()
