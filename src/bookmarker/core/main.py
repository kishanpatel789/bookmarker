import logging

from .database import DatabaseRepository, get_repo
from .exceptions import ArtifactNotFoundError, ContentFetchError, ContentSummaryError
from .fetchers import ContentFetcher, TrafilaturaFetcher, YouTubeFetcher
from .models import Artifact, ArtifactTypeEnum
from .summarizers import ContentSummarizer, get_summarizer

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
    except ContentFetchError:
        logging.error(f"Error fetching content for artifact ID {artifact_id}")
        raise


def store_content(
    repo: DatabaseRepository,
    artifact_id: int,
    content: str,
    *,
    content_type: str = "raw",
) -> Artifact:
    if content_type == "raw":
        artifact = repo.store_content_raw(artifact_id, content)
    if content_type == "summary":
        artifact = repo.store_content_summary(artifact_id, content)

    return artifact


def get_and_store_content(
    repo: DatabaseRepository, artifact_id: int
) -> Artifact | None:
    content = get_content(repo, artifact_id)
    if content is not None:
        artifact = store_content(repo, artifact_id, content, content_type="raw")
        return artifact


def get_content_summary(
    repo: DatabaseRepository, summarizer: ContentSummarizer, artifact_id: int
) -> str | None:
    artifact = repo.get(artifact_id)
    if artifact is None:
        raise ArtifactNotFoundError(f"Artifact with ID {artifact_id} not found.")

    try:
        summary = summarizer.summarize(artifact.content_raw)
        return summary
    except ContentSummaryError:
        logging.exception(f"Error summarizing content for artifact ID {artifact_id}")
        raise


def main():
    repo = get_repo()
    repo.create_db_and_tables()


if __name__ == "__main__":  # pragma: no cover
    main()

    # test ground
    from .database import get_repo
    from .summarizers import get_summarizer

    repo = get_repo()
    summarizer = get_summarizer()

    url = "https://kpdata.dev/blog/python-slicing/"
    artifact = get_or_create_artifact(repo, "Python Slicing", url)
    get_and_store_content(repo, artifact.id)

    summary = get_content_summary(repo, summarizer, artifact.id)
    store_content(repo, artifact.id, summary, content_type="summary")
