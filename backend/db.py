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


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def reset_db() -> None:
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
