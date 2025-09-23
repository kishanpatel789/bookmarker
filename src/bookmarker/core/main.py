import logging

from trafilatura import extract, fetch_url

from .database import DatabaseRepository, create_db_and_tables
from .exceptions import ArtifactNotFoundError, ContentFetchError
from .models import Artifact, ArtifactTypeEnum


def add_artifact(
    repo: DatabaseRepository,
    title: str,
    url: str,
    artifact_type: ArtifactTypeEnum = ArtifactTypeEnum.ARTICLE,
) -> Artifact:
    existing_artifact = repo.get_by_url(url)
    if existing_artifact is not None:
        logging.info(
            f"Artifact with URL '{url}' already exists with ID {existing_artifact.id}."
        )
        return existing_artifact

    artifact = Artifact(
        title=title,
        url=url,
        artifact_type=artifact_type,
    )
    repo.add(artifact)

    return artifact


def get_content(repo: DatabaseRepository, artifact_id: int) -> str | None:
    artifact = repo.get(artifact_id)
    if artifact is None:
        raise ArtifactNotFoundError(f"Artifact with ID {artifact_id} not found.")

    downloaded = fetch_url(artifact.url)
    if downloaded is None:
        raise ContentFetchError(f"Failed to fetch content from URL: {artifact.url}")

    return extract(
        downloaded,
        include_images=True,
        include_tables=True,
        include_links=True,
        output_format="markdown",
    )


def store_content(repo: DatabaseRepository, artifact_id: int, content: str) -> Artifact:
    artifact = repo.store_content_raw(artifact_id, content)
    return artifact


def get_and_store_content(
    repo: DatabaseRepository, artifact_id: int
) -> Artifact | None:
    content = get_content(repo, artifact_id)
    artifact = store_content(repo, artifact_id, content)
    return artifact


def main():
    create_db_and_tables()


if __name__ == "__main__":
    # main()

    # test ground
    url = "https://kpdata.dev/blog/python-slicing/"
    artifact = add_artifact("Python Slicing", url)
    get_and_store_content(artifact.id)
