"""La mini-migracion de db.py: una base creada ANTES de las columnas de la
Caja de Cristal no debe romper la app (create_all no agrega columnas)."""
import os
import tempfile

from sqlalchemy import create_engine, inspect, text

from backend.db import _migrate_missing_columns


def _old_schema_engine(path: str):
    engine = create_engine(f"sqlite:///{path}")
    with engine.begin() as conn:
        # Esquema de main ANTES de la rama (sin execution_trace/attribution/
        # executive_summary).
        conn.execute(
            text(
                "CREATE TABLE signal (id VARCHAR PRIMARY KEY, news_id VARCHAR, "
                "instrument VARCHAR, impact VARCHAR, confidence FLOAT, evidence JSON, "
                "sources JSON, price_comparison JSON, disclaimer VARCHAR, "
                "suggested_action VARCHAR, created_at DATETIME, review_status VARCHAR, "
                "review_justification VARCHAR, reviewed_at DATETIME)"
            )
        )
        conn.execute(
            text(
                "CREATE TABLE taskalert (id VARCHAR PRIMARY KEY, signal_id VARCHAR, "
                "instrument VARCHAR, title VARCHAR, description VARCHAR, "
                "status VARCHAR, created_at DATETIME)"
            )
        )
    return engine


def test_migration_adds_missing_columns_and_is_idempotent():
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "old.db")
        engine = _old_schema_engine(path)

        _migrate_missing_columns(engine)
        _migrate_missing_columns(engine)  # segunda pasada: no debe fallar

        inspector = inspect(engine)
        signal_cols = {c["name"] for c in inspector.get_columns("signal")}
        task_cols = {c["name"] for c in inspector.get_columns("taskalert")}
        assert {"execution_trace", "attribution", "review_cause"} <= signal_cols
        assert "executive_summary" in task_cols

        # La consulta que antes daba OperationalError ahora funciona.
        with engine.connect() as conn:
            conn.execute(text("SELECT execution_trace, attribution FROM signal")).fetchall()

        # En Windows, sqlite mantiene el archivo abierto hasta que se libera el
        # engine; sin esto, TemporaryDirectory falla al limpiar (PermissionError).
        engine.dispose()
