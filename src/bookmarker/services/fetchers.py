import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Final

from ..core.config import get_timeout_multithreading
from ..core.database import DatabaseRepository
from ..core.exceptions import ArtifactNotFoundError, ContentFetchError
from ..core.fetchers import ContentFetcher, TrafilaturaFetcher, YouTubeFetcher
from ..core.models import Artifact, ArtifactTypeEnum
from .base import ContentType, store_content

logger = logging.getLogger(__name__)


FETCHERS = {
    ArtifactTypeEnum.ARTICLE: TrafilaturaFetcher,
    ArtifactTypeEnum.YOUTUBE: YouTubeFetcher,
}


def fetch_content(artifact_id: int, *, repo: DatabaseRepository) -> str | None:
    artifact = repo.get(artifact_id)
    if artifact is None:
        raise ArtifactNotFoundError(f"Artifact with ID {artifact_id} not found.")

    try:
        fetcher: ContentFetcher = FETCHERS[artifact.artifact_type]()
        content = fetcher.fetch(artifact.url)
        return content
    except ContentFetchError:
        logger.exception(f"Error fetching content for artifact ID {artifact_id}")
        raise


def fetch_and_store_content(
    artifact_id: int, *, repo: DatabaseRepository
) -> Artifact | None:
    content = fetch_content(artifact_id, repo=repo)
    if content is not None:
        artifact = store_content(
            repo, artifact_id, content, content_type=ContentType.RAW
        )
        return artifact


def fetch_and_store_content_many(
    artifact_ids: list[int], *, repo: DatabaseRepository, max_workers: int = 5
) -> dict:
    results = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_id = {}
        for a_id in artifact_ids:
            future = executor.submit(fetch_and_store_content, a_id, repo=repo)
            future_to_id[future] = a_id
        try:
            timeout_multithreading: Final[int] = get_timeout_multithreading()
            for future in as_completed(future_to_id, timeout=timeout_multithreading):
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
