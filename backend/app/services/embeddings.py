import hashlib
import json
import logging
import math
import os
import re
from urllib.error import URLError
from urllib.request import Request, urlopen

EMBEDDING_DIMENSIONS = 384
TOKEN_PATTERN = re.compile(r"[a-zA-Z][a-zA-Z'-]+")
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434').rstrip('/')
OLLAMA_EMBEDDING_MODEL = os.getenv('OLLAMA_EMBEDDING_MODEL', 'nomic-embed-text')
logger = logging.getLogger(__name__)


class EmbeddingsService:
    def embed_text(self, text: str) -> list[float]:
        embedding = self._ollama_embedding(text)
        if embedding:
            return embedding
        return self._hash_embedding(text)

    def embed_documents(self, documents: list[str]) -> list[list[float]]:
        return [self.embed_text(document) for document in documents]

    def _ollama_embedding(self, text: str) -> list[float] | None:
        payload = {
            'model': OLLAMA_EMBEDDING_MODEL,
            'prompt': text,
        }
        try:
            request = Request(
                f'{OLLAMA_BASE_URL}/api/embeddings',
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                method='POST',
            )
            with urlopen(request, timeout=45) as response:
                data = json.loads(response.read().decode('utf-8'))
                embedding = data.get('embedding')
                if isinstance(embedding, list) and embedding:
                    return [float(value) for value in embedding]
        except (OSError, URLError, json.JSONDecodeError, TypeError, ValueError) as exc:
            logger.warning('Ollama embeddings unavailable; using hash fallback: %s', exc)
        return None

    def _hash_embedding(self, text: str) -> list[float]:
        vector = [0.0] * EMBEDDING_DIMENSIONS
        tokens = TOKEN_PATTERN.findall(text.lower())

        for token in tokens:
            digest = hashlib.sha256(token.encode('utf-8')).digest()
            index = int.from_bytes(digest[:4], 'big') % EMBEDDING_DIMENSIONS
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector

        return [value / norm for value in vector]
