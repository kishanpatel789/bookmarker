import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from enum import Enum, auto

from .config import set_up_logging
from .database import DatabaseRepository, get_repo
from .exceptions import ArtifactNotFoundError, ContentFetchError, ContentSummaryError
from .fetchers import ContentFetcher, TrafilaturaFetcher, YouTubeFetcher
from .models import Artifact, ArtifactTypeEnum
from .summarizers import ContentSummarizer

FETCHERS = {
    ArtifactTypeEnum.ARTICLE: TrafilaturaFetcher,
    ArtifactTypeEnum.YOUTUBE: YouTubeFetcher,
}

TIMEOUT_MULTITHREADING = 10

set_up_logging()
logger = logging.getLogger(__name__)


class ContentType(Enum):
    RAW = auto()
    SUMMARY = auto()


def get_or_create_artifact(
    repo: DatabaseRepository,
    title: str,
    url: str,
    artifact_type: ArtifactTypeEnum = ArtifactTypeEnum.ARTICLE,
) -> Artifact:
    existing_artifact = repo.get_by_url(url)
    if existing_artifact is not None:
        logger.info(
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


def fetch_content(repo: DatabaseRepository, artifact_id: int) -> str | None:
    artifact = repo.get(artifact_id)
    if artifact is None:
        raise ArtifactNotFoundError(f"Artifact with ID {artifact_id} not found.")

    try:
        fetcher: ContentFetcher = FETCHERS[artifact.artifact_type]()
        content = fetcher.fetch(artifact.url)
        return content
    except ContentFetchError:
        logger.error(f"Error fetching content for artifact ID {artifact_id}")
        raise


def store_content(
    repo: DatabaseRepository,
    artifact_id: int,
    content: str,
    *,
    content_type: ContentType = ContentType.RAW,
) -> Artifact:
    match content_type:
        case ContentType.RAW:
            artifact = repo.store_content_raw(artifact_id, content)
        case ContentType.SUMMARY:
            artifact = repo.store_content_summary(artifact_id, content)
        case _:
            raise ValueError(f"Unsupported content type: {content_type}")
    return artifact


def fetch_and_store_content(
    repo: DatabaseRepository, artifact_id: int
) -> Artifact | None:
    content = fetch_content(repo, artifact_id)
    if content is not None:
        artifact = store_content(
            repo, artifact_id, content, content_type=ContentType.RAW
        )
        return artifact


def fetch_and_store_content_many(
    repo: DatabaseRepository, artifact_ids: list[int], max_workers: int = 5
) -> dict:
    results = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_id = {}
        for a_id in artifact_ids:
            future = executor.submit(fetch_and_store_content, repo, a_id)
            future_to_id[future] = a_id
        try:
            for future in as_completed(future_to_id, timeout=TIMEOUT_MULTITHREADING):
                a_id = future_to_id[future]
                try:
                    future.result()
                    results[a_id] = "ok"
                except ArtifactNotFoundError:
                    results[a_id] = "not_found"
                except ContentFetchError:
                    results[a_id] = "fetch_error"
                except Exception as e:
                    results[a_id] = f"exception: {e}"
        except TimeoutError:
            logger.error(
                "Timeout error. Considering increasing TIMEOUT_MULTITHREADING."
            )
            raise
    return results


def summarize_content(
    repo: DatabaseRepository, summarizer: ContentSummarizer, artifact_id: int
) -> str | None:
    artifact = repo.get(artifact_id)
    if artifact is None:
        raise ArtifactNotFoundError(f"Artifact with ID {artifact_id} not found.")

    try:
        summary = summarizer.summarize(artifact.content_raw)
        return summary
    except ContentSummaryError:
        logger.exception(f"Error summarizing content for artifact ID {artifact_id}")
        raise


def summarize_and_store_content(
    repo: DatabaseRepository, summarizer: ContentSummarizer, artifact_id: int
) -> Artifact | None:
    summary = summarize_content(repo, summarizer, artifact_id)
    if summary is not None:
        artifact = store_content(
            repo, artifact_id, summary, content_type=ContentType.SUMMARY
        )
        return artifact


def main():
    repo = get_repo()
    repo.create_db_and_tables()


if __name__ == "__main__":  # pragma: no cover
    main()

    # scratch work
    repo = get_repo()
    results = fetch_and_store_content_many(repo, [1, 2, 3, 4])
