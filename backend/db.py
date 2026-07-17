from sqlalchemy import text
from sqlalchemy.exc import DatabaseError
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from backend.config import DATABASE_URL

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
# sqlite in-memory necesita StaticPool para compartir la misma conexion/DB entre
# requests (usado en tests, para evitar locks de archivo en Windows).
if DATABASE_URL == "sqlite:///:memory:":
    engine = create_engine(DATABASE_URL, connect_args=connect_args, poolclass=StaticPool)
else:
    engine = create_engine(DATABASE_URL, connect_args=connect_args)

# Columnas agregadas despues del primer despliegue. create_all NO agrega
# columnas a tablas ya existentes: sin esto, una base creada antes (app.db
# local o el Postgres de Neon) devuelve 500 en todos los endpoints de senales.
_NEW_COLUMNS = [
    ("signal", "execution_trace", "JSON"),
    ("signal", "attribution", "JSON"),
    ("taskalert", "executive_summary", "JSON"),
]


def _migrate_missing_columns(target_engine) -> None:
    """Mini-migracion best-effort: ALTER por columna nueva; si ya existe, el
    motor lo rechaza y se ignora. Funciona igual en sqlite y Postgres/Neon."""
    for table, column, column_type in _NEW_COLUMNS:
        try:
            with target_engine.begin() as conn:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}"))
        except DatabaseError:
            pass


def init_db() -> None:
    SQLModel.metadata.create_all(engine)
    _migrate_missing_columns(engine)


def reset_db() -> None:
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
