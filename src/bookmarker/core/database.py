from typing import Sequence

from sqlmodel import Session, SQLModel, create_engine, select

from .config import DATABASE_URL, DEBUG
from .exceptions import ArtifactNotFoundError
from .models import Artifact


class DatabaseRepository:
    def __init__(self, database_url: str, echo: bool = False) -> None:
        self._engine = create_engine(database_url, echo=echo)

    def create_db_and_tables(self) -> None:
        SQLModel.metadata.create_all(self._engine)

    def add(self, artifact: Artifact) -> None:
        with Session(self._engine) as session:
            session.add(artifact)
            session.commit()
            session.refresh(artifact)

    def list(self) -> Sequence[Artifact]:
        with Session(self._engine) as session:
            return session.exec(select(Artifact)).all()

    def get(self, artifact_id: int) -> Artifact | None:
        with Session(self._engine) as session:
            return session.get(Artifact, artifact_id)

    def get_by_url(self, url: str) -> Artifact | None:
        with Session(self._engine) as session:
            statement = select(Artifact).where(Artifact.url == url)
            return session.exec(statement).first()

    def delete(self, artifact_id: int) -> None:
        with Session(self._engine) as session:
            artifact = session.get(Artifact, artifact_id)
            if artifact is None:
                raise ArtifactNotFoundError(
                    f"Artifact with ID {artifact_id} not found."
                )
            session.delete(artifact)
            session.commit()

    def store_content_raw(self, artifact_id: int, content: str) -> Artifact:
        artifact = self.get(artifact_id)
        if artifact is None:
            raise ArtifactNotFoundError(f"Artifact with ID {artifact_id} not found.")
        with Session(self._engine) as session:
            artifact.content_raw = content
            session.add(artifact)
            session.commit()
            session.refresh(artifact)
        return artifact

    def store_content_summary(self, artifact_id: int, content: str) -> Artifact:
        artifact = self.get(artifact_id)
        if artifact is None:
            raise ArtifactNotFoundError(f"Artifact with ID {artifact_id} not found.")
        with Session(self._engine) as session:
            artifact.content_summary = content
            session.add(artifact)
            session.commit()
            session.refresh(artifact)
        return artifact


def get_repo() -> DatabaseRepository:
    return DatabaseRepository(database_url=DATABASE_URL, echo=DEBUG)
