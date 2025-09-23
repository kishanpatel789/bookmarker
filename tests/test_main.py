from src.bookmarker.core.main import add_artifact


def test_add_artifact(db_repo):
    artifact = add_artifact(db_repo, title="Test Article", url="https://example.com")

    assert artifact.id is not None
    assert artifact.title == "Test Article"
    assert artifact.url == "https://example.com"
    assert artifact.artifact_type.name == "ARTICLE"
