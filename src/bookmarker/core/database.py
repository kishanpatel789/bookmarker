from typing import Sequence

from sqlalchemy import Engine  # for typing
from sqlmodel import Session, SQLModel, create_engine, select

from .config import DATABASE_URL, DEBUG
from .exceptions import ArtifactNotFoundError
from .models import Artifact


def create_db_and_tables():
    engine = create_engine(DATABASE_URL, echo=DEBUG)
    SQLModel.metadata.create_all(engine)


class DatabaseRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def add(self, artifact: Artifact) -> None:
        with Session(self._engine) as session:
            session.add(artifact)
            session.commit()
            session.refresh(artifact)

    def list(self) -> Sequence[Artifact]:
        with Session(self._engine) as session:
            artifacts = session.exec(select(Artifact)).all()
        return artifacts

    def get(self, artifact_id: int) -> Artifact | None:
        with Session(self._engine) as session:
            artifact = session.get(Artifact, artifact_id)
        return artifact

    def get_by_url(self, url: str) -> Artifact | None:
        with Session(self._engine) as session:
            statement = select(Artifact).where(Artifact.url == url)
            artifact = session.exec(statement).first()
        return artifact

    def delete(self, artifact_id: int) -> None:
        with Session(self._engine) as session:
            artifact = session.get(Artifact, artifact_id)
            if artifact is not None:
                session.delete(artifact)
                session.commit()
            else:
                raise ArtifactNotFoundError(
                    f"Artifact with ID {artifact_id} not found."
                )

    def store_content_raw(self, artifact_id: int, content: str) -> Artifact:
        artifact = self.get(artifact_id)

        with Session(self._engine) as session:
            artifact.content_raw = content
            session.add(artifact)
            session.commit()
            session.refresh(artifact)
        return artifact
