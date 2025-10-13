import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Final

from ..core.config import get_timeout_multithreading
from ..core.database import DatabaseRepository
from ..core.exceptions import (
    ArtifactNotFoundError,
    ContentSummaryError,
    ContentSummaryExistsWarning,
    InvalidAPIKeyError,
)
from ..core.models import Artifact
from ..core.summarizers import ContentSummarizer, get_summarizer
from .base import ContentType, store_content

logger = logging.getLogger(__name__)


def summarize_content(
    artifact_id: int,
    *,
    repo: DatabaseRepository,
    summarizer: ContentSummarizer,
    refresh: bool = False,
) -> str | None:
    artifact = repo.get(artifact_id)
    if artifact is None:
        raise ArtifactNotFoundError(f"Artifact with ID {artifact_id} not found.")

    if (refresh is False) and (artifact.content_summary is not None):
        raise ContentSummaryExistsWarning(
            f"Summary already exists for artifact {artifact_id}"
        )

    try:
        summary = summarizer.summarize(artifact.content_raw)
        return summary
    except (ContentSummaryError, InvalidAPIKeyError):
        logger.exception(f"Error summarizing content for artifact ID {artifact_id}")
        raise


def summarize_and_store_content(
    artifact_id: int,
    *,
    repo: DatabaseRepository,
    summarizer: ContentSummarizer | None = None,
    refresh: bool = False,
) -> Artifact | None:
    if summarizer is None:
        summarizer = get_summarizer()
    summary = summarize_content(
        artifact_id, repo=repo, summarizer=summarizer, refresh=refresh
    )
    if summary is not None:
        artifact = store_content(
            repo, artifact_id, summary, content_type=ContentType.SUMMARY
        )
        return artifact


def summarize_and_store_content_many(
    artifact_ids: list[int],
    *,
    repo: DatabaseRepository,
    max_workers: int = 5,
) -> dict:
    summarizer = get_summarizer()
    timeout_multithreading: Final[int] = get_timeout_multithreading()
    results = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_id = {}
        for a_id in artifact_ids:
            future = executor.submit(
                summarize_and_store_content, a_id, repo=repo, summarizer=summarizer
            )
            future_to_id[future] = a_id
        try:
            for future in as_completed(future_to_id, timeout=timeout_multithreading):
                a_id = future_to_id[future]
                try:
                    future.result()
                    results[a_id] = "ok"
                except ArtifactNotFoundError:
                    results[a_id] = "not_found"
                except ContentSummaryError:
                    results[a_id] = "summarize_error"
                except Exception as e:
                    results[a_id] = f"exception: {e}"
        except TimeoutError:
            logger.error(
                "Timeout error. Considering increasing TIMEOUT_MULTITHREADING."
            )
            raise
    return results
