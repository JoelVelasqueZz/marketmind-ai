import os

# Deben fijarse ANTES de importar backend.config (que lee os.getenv al importarse).
# sqlite in-memory (con StaticPool en backend/db.py) evita locks de archivo en Windows.
os.environ["LLM_MODE"] = "mock"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["CORS_ORIGINS"] = "http://localhost:5173"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from backend.db import reset_db  # noqa: E402
from backend.main import app  # noqa: E402


@pytest.fixture()
def client():
    reset_db()
    with TestClient(app) as c:
        yield c
