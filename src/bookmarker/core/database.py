from datetime import datetime, timezone
from typing import Sequence

from sqlmodel import Session, create_engine, select

from .config import get_config
from .exceptions import ArtifactNotFoundError
from .models import Artifact, SQLModel, Tag


class DatabaseRepository:
    def __init__(self, database_url: str, echo: bool = False) -> None:
        self._engine = create_engine(database_url, echo=echo)

    def create_db_and_tables(self) -> None:
        SQLModel.metadata.create_all(self._engine)

    def _store_artifact(self, artifact: Artifact) -> None:
        artifact.updated_at = datetime.now(timezone.utc)
        with Session(self._engine) as session:
            session.add(artifact)
            session.commit()
            session.refresh(artifact)

    def add(self, artifact: Artifact) -> None:
        self._store_artifact(artifact)

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
        artifact.content_raw = content
        self._store_artifact(artifact)
        return artifact

    def store_content_summary(self, artifact_id: int, content: str) -> Artifact:
        artifact = self.get(artifact_id)
        if artifact is None:
            raise ArtifactNotFoundError(f"Artifact with ID {artifact_id} not found.")
        artifact.content_summary = content
        self._store_artifact(artifact)
        return artifact

    def tag(self, artifact_id: int, /, *tags: Tag, remove: bool = False) -> Artifact:
        """Updates the artifact's tags in-place. Modifies artifact.tags and updated_at.
        Method either adds tags provided or removes tags provided depending on `remove`.

        Args:
            artifact_id (int): ID of artifact on which to update tags
            tags (tuple[Tag]): tags to either add or remove (depending on `remove`)
            remove (bool): if True, remove tags listed in `tags` argument; else add tags

        Returns:
            Artifact: updated artifact object
        """
        artifact = self.get(artifact_id)
        if artifact is None:
            raise ArtifactNotFoundError

        # get existing tags from database, to avoid duplicate tag creation
        tag_names = {tag.name for tag in tags}
        with Session(self._engine) as session:
            existing_tags = session.exec(
                select(Tag).where(Tag.name.in_(tag_names))
            ).all()
            existing_tags_dict = {tag.name: tag for tag in existing_tags}
            tags_synced = tuple(existing_tags_dict.get(tag.name, tag) for tag in tags)

        current_tags: dict[str, Tag] = {tag.name: tag for tag in artifact.tags}
        incoming_tags: dict[str, Tag] = {tag.name: tag for tag in tags_synced}
        if remove:
            updated_tags = [
                tag
                for tag_name, tag in current_tags.items()
                if tag_name not in incoming_tags
            ]
        else:
            updated_tags = list(current_tags.values())
            for tag_name, tag in incoming_tags.items():
                if tag_name not in current_tags:
                    updated_tags.append(tag)

        artifact.tags = updated_tags
        self._store_artifact(artifact)
        return artifact


def get_repo() -> DatabaseRepository:
    # read env vars locally to allow test overrides for cli
    try:
        config = get_config()
    except FileNotFoundError:
        raise RuntimeError("Configuration file not found.")

    database_url = config("DATABASE_URL")
    debug = config("DEBUG", cast=bool, default=False)
    return DatabaseRepository(database_url=database_url, echo=debug)
