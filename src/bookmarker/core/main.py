from sqlmodel import Session
from trafilatura import extract, fetch_url

from .database import create_db_and_tables, engine
from .models import Artifact, ArtifactTypeEnum


def add_artifact(title, url, artifact_type=ArtifactTypeEnum.ARTICLE):
    artifact = Artifact(
        title=title,
        url=url,
        artifact_type=artifact_type,
    )

    with Session(engine) as session:
        session.add(artifact)
        session.commit()
        session.refresh(artifact)

    return artifact


def get_content(artifact_id):
    with Session(engine) as session:
        artifact = session.get(Artifact, artifact_id)
        if artifact is None:
            return None

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


def store_content(artifact_id, content):
    with Session(engine) as session:
        artifact = session.get(Artifact, artifact_id)
        if artifact is None:
            return None
        artifact.content_raw = content
        session.add(artifact)
        session.commit()
        session.refresh(artifact)
    return artifact


def main():
    create_db_and_tables()


if __name__ == "__main__":
    # main()
    url = "https://kpdata.dev/blog/python-slicing/"

    artifact = add_artifact("Python Slicing", url)
    content = get_content(artifact.id)
    if content:
        store_content(artifact.id, content)
        print(f"Content stored for artifact ID {artifact.id}")
    else:
        print("Failed to retrieve content.")
