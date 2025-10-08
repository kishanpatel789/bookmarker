import logging
from enum import Enum, auto

from ..core.database import DatabaseRepository
from ..core.models import Artifact, ArtifactTypeEnum, Tag

logger = logging.getLogger(__name__)


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


class ContentType(Enum):
    RAW = auto()
    SUMMARY = auto()


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


def update_tags(
    repo: DatabaseRepository,
    artifact_id: int,
    tags: list[str],
    *,
    remove: bool,
) -> Artifact:
    tag_objs = [Tag(name=tag) for tag in tags]
    artifact = repo.tag(artifact_id, *tag_objs, remove=remove)
    return artifact
