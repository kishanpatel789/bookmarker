import re
from datetime import datetime, timezone
from enum import StrEnum

from pydantic import ConfigDict, field_validator
from sqlalchemy import Column
from sqlalchemy import Enum as SaEnum
from sqlmodel import Field, Relationship, SQLModel


def enum_column(enum_cls):
    """A SQLAlchemy column that properly returns ENUM values instead of labels"""
    return Column(SaEnum(enum_cls, values_callable=lambda x: [e.value for e in x]))


class ArtifactTypeEnum(StrEnum):
    ARTICLE = "article"
    YOUTUBE = "youtube"


class ArtifactTagLink(SQLModel, table=True):
    artifact_id: int | None = Field(
        default=None, foreign_key="artifact.id", primary_key=True
    )
    tag_id: int | None = Field(default=None, foreign_key="tag.id", primary_key=True)


class Artifact(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(index=True, min_length=1, max_length=200)
    url: str = Field(index=True, min_length=5)
    artifact_type: ArtifactTypeEnum = Field(
        default=ArtifactTypeEnum.ARTICLE, sa_column=enum_column(ArtifactTypeEnum)
    )
    notes: str | None = None
    content_raw: str | None = None
    content_summary: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime | None = None

    tags: list["Tag"] = Relationship(
        back_populates="artifacts",
        link_model=ArtifactTagLink,
        sa_relationship_kwargs={
            "lazy": "selectin",
        },
    )


class Tag(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True, min_length=1, max_length=20)

    artifacts: list["Artifact"] = Relationship(
        back_populates="tags", link_model=ArtifactTagLink
    )

    @field_validator("name", mode="before")
    @classmethod
    def clean_tag_name(cls, value: str) -> str:
        value = value.strip().lower()
        value = re.sub(r"\s+", "-", value)
        return value

    model_config = ConfigDict(validate_assignment=True)
