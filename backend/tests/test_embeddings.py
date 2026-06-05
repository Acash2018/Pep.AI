from urllib.error import URLError

from app.services.embeddings import EMBEDDING_DIMENSIONS, EmbeddingsService


def test_embeddings_fall_back_to_deterministic_vector_when_ollama_is_unavailable(monkeypatch):
    def fake_urlopen(*args, **kwargs):
        raise URLError('connection refused')

    monkeypatch.setattr('app.services.embeddings.urlopen', fake_urlopen)

    vector = EmbeddingsService().embed_text('press resistant ball-playing center back')

    assert len(vector) == EMBEDDING_DIMENSIONS
    assert any(value != 0 for value in vector)
