import logging

from .database import DatabaseRepository, get_repo
from .exceptions import ArtifactNotFoundError, ContentFetchError
from .fetchers import ContentFetcher, TrafilaturaFetcher, YouTubeFetcher
from .models import Artifact, ArtifactTypeEnum

FETCHERS = {
    ArtifactTypeEnum.ARTICLE: TrafilaturaFetcher,
    ArtifactTypeEnum.YOUTUBE: YouTubeFetcher,
}


def get_or_create_artifact(
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

    try:
        fetcher: ContentFetcher = FETCHERS[artifact.artifact_type]()
        content = fetcher.fetch(artifact.url)
        return content
    except ContentFetchError as e:
        logging.error(f"Error fetching content for artifact ID {artifact_id}: {e}")
        raise


def store_content(repo: DatabaseRepository, artifact_id: int, content: str) -> Artifact:
    artifact = repo.store_content_raw(artifact_id, content)
    return artifact


def get_and_store_content(
    repo: DatabaseRepository, artifact_id: int
) -> Artifact | None:
    content = get_content(repo, artifact_id)
    if content is not None:
        artifact = store_content(repo, artifact_id, content)
        return artifact


def main():
    repo = get_repo()
    repo.create_db_and_tables()


if __name__ == "__main__":  # pragma: no cover
    main()

    # test ground
    # from .database import get_repo
    # repo = get_repo()
    # url = "https://kpdata.dev/blog/python-slicing/"
    # artifact = get_or_create_artifact(repo, "Python Slicing", url)
    # get_and_store_content(repo, artifact.id)
