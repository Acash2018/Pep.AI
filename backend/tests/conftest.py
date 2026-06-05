import os
import tempfile

import pytest

_test_db = tempfile.NamedTemporaryFile(prefix='pep_ai_test_', suffix='.db', delete=False)
_test_db.close()
os.environ['DATABASE_URL'] = f"sqlite:///{_test_db.name}"
os.environ.setdefault('OLLAMA_BASE_URL', 'http://127.0.0.1:11434')


@pytest.fixture(autouse=True)
def reset_database():
    from app.db import models  # noqa: F401
    from app.db.session import Base, engine

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
