import logging

from sqlmodel import select
from trafilatura import extract, fetch_url

from .database import create_db_and_tables, get_session
from .exceptions import ArtifactNotFoundError
from .models import Artifact, ArtifactTypeEnum


def add_artifact(
    title: str, url: str, artifact_type: ArtifactTypeEnum = ArtifactTypeEnum.ARTICLE
) -> Artifact:
    with get_session() as session:
        statement = select(Artifact).where(Artifact.url == url)
        existing_artifact = session.exec(statement).first()
        if existing_artifact:
            logging.info(
                f"Artifact with URL '{url}' already exists with ID {existing_artifact.id}."
            )
            return existing_artifact

    artifact = Artifact(
        title=title,
        url=url,
        artifact_type=artifact_type,
    )

    with get_session() as session:
        session.add(artifact)
        session.commit()
        session.refresh(artifact)

    return artifact


def get_artifact(artifact_id: int) -> Artifact:
    with get_session() as session:
        artifact = session.get(Artifact, artifact_id)
        if artifact is None:
            raise ArtifactNotFoundError(f"Artifact with ID {artifact_id} not found.")
    return artifact


def get_content(artifact_id: int) -> str | None:
    artifact = get_artifact(artifact_id)

    downloaded = fetch_url(artifact.url)
    if downloaded is not None:
        return extract(
            downloaded,
            include_images=True,
            include_tables=True,
            include_links=True,
            output_format="markdown",
        )
    return None


def store_content(artifact_id: int, content: str) -> Artifact:
    artifact = get_artifact(artifact_id)

    with get_session() as session:
        artifact.content_raw = content
        session.add(artifact)
        session.commit()
        session.refresh(artifact)
    return artifact


def main():
    create_db_and_tables()


if __name__ == "__main__":
    # main()

    # test ground
    url = "https://kpdata.dev/blog/python-slicing/"
    artifact = add_artifact("Python Slicing", url)
    content = get_content(artifact.id)
    if content:
        store_content(artifact.id, content)
        logging.debug(f"Content stored for artifact ID {artifact.id}")
    else:
        logging.debug("Failed to retrieve content.")
