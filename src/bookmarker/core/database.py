from contextlib import contextmanager

from sqlmodel import Session, SQLModel, create_engine

from .config import DATABASE_URL, DEBUG

engine = create_engine(DATABASE_URL, echo=DEBUG)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


@contextmanager
def get_session():
    with Session(engine) as session:
        yield session
