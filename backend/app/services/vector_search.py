from typing import Any

from app.services.embeddings import EmbeddingsService, OLLAMA_EMBEDDING_MODEL
from app.utils.chromadb_client import get_collection

COLLECTION_NAME = f"football_knowledge_base_{OLLAMA_EMBEDDING_MODEL.replace(':', '_').replace('.', '_')}"


class VectorSearchService:
    def __init__(self, embeddings_service: EmbeddingsService | None = None):
        self.embeddings_service = embeddings_service or EmbeddingsService()

    def upsert_documents(self, documents: list[dict[str, Any]]) -> int:
        if not documents:
            return 0

        collection = get_collection(COLLECTION_NAME)
        ids = [document['id'] for document in documents]
        texts = [document['text'] for document in documents]
        embeddings = self.embeddings_service.embed_documents(texts)
        metadatas = [document['metadata'] for document in documents]

        collection.upsert(ids=ids, documents=texts, embeddings=embeddings, metadatas=metadatas)
        return len(documents)

    def search(self, query: str, limit: int = 5, category: str | None = None) -> list[dict[str, Any]]:
        collection = get_collection(COLLECTION_NAME)
        query_embedding = self.embeddings_service.embed_text(query)
        where = {'category': category} if category else None
        results = collection.query(query_embeddings=[query_embedding], n_results=limit, where=where)

        matches = []
        ids = results.get('ids', [[]])[0]
        documents = results.get('documents', [[]])[0]
        metadatas = results.get('metadatas', [[]])[0]
        distances = results.get('distances', [[]])[0]

        for index, document_id in enumerate(ids):
            matches.append(
                {
                    'id': document_id,
                    'text': documents[index],
                    'metadata': metadatas[index],
                    'distance': distances[index] if index < len(distances) else None,
                }
            )

        return matches
