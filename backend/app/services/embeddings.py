import hashlib
import math
import re

EMBEDDING_DIMENSIONS = 384
TOKEN_PATTERN = re.compile(r"[a-zA-Z][a-zA-Z'-]+")


class EmbeddingsService:
    def embed_text(self, text: str) -> list[float]:
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

    def embed_documents(self, documents: list[str]) -> list[list[float]]:
        return [self.embed_text(document) for document in documents]
