import os

try:
    import chromadb
except ImportError:  # pragma: no cover - optional vector-store integration
    chromadb = None

PERSIST_DIR = os.getenv('CHROMA_PERSIST_DIR', './chromadb')


def _get_client():
    if chromadb is None:
        raise RuntimeError('Install chromadb to use vector-store collections.')

    return chromadb.PersistentClient(path=PERSIST_DIR)


def get_collection(name: str):
    return _get_client().get_or_create_collection(name=name)
