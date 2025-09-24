from unittest.mock import patch

import pytest

from src.bookmarker.core.exceptions import ContentFetchError
from src.bookmarker.core.fetchers import (
    ContentFetcher,
    TrafilaturaFetcher,
)


def test_contentfetcher_is_abstract():
    with pytest.raises(TypeError):
        ContentFetcher()


@patch("src.bookmarker.core.fetchers.extract")
@patch("src.bookmarker.core.fetchers.fetch_url")
def test_trafilaturafetcher_fetch_success(mock_fetch_url, mock_extract):
    mock_fetch_url.return_value = "<html><head></head><body><h1>Test</h1></body></html>"
    mock_extract.return_value = "Test"

    fetcher = TrafilaturaFetcher()
    content = fetcher.fetch("https://example.com")

    assert content == "Test"
    mock_fetch_url.assert_called_once_with("https://example.com")
    mock_extract.assert_called_once()


@patch("src.bookmarker.core.fetchers.fetch_url")
def test_trafilaturafetcher_fetch_failure(mock_fetch_url):
    mock_fetch_url.return_value = None

    fetcher = TrafilaturaFetcher()

    with pytest.raises(ContentFetchError) as exc:
        fetcher.fetch("https://example.com")
    assert "Failed to fetch content from URL" in str(exc.value)
