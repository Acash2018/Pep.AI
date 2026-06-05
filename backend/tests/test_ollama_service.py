from urllib.error import URLError

from app.services.ollama_service import OllamaFailureKind, OllamaService


def test_ollama_completion_classifies_unavailable_service(monkeypatch):
    def fake_urlopen(*args, **kwargs):
        raise URLError('connection refused')

    monkeypatch.setattr('app.services.ollama_service.urlopen', fake_urlopen)

    result = OllamaService()._chat_completion('system', {'player': {}}, json_output=False)

    assert result.content is None
    assert result.failure_kind == OllamaFailureKind.UNAVAILABLE
    assert 'connection refused' in result.detail
