import pytest

from src.bookmarker.core.main import add_artifact


@pytest.mark.focus()
def test_add_artifact():
    artifact = add_artifact(title="Test Article", url="https://example.com")

    assert artifact.id is not None
    assert artifact.title == "Test Article"
    assert artifact.url == "https://example.com"
    assert artifact.artifact_type.name == "ARTICLE"
