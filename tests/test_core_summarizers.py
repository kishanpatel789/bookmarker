from unittest.mock import Mock, patch

import pytest

from src.bookmarker.core import summarizers
from src.bookmarker.core.summarizers import (
    AgentRunError,
    ContentSummarizer,
    ContentSummaryError,
    InvalidAPIKeyError,
    InvalidContentError,
    ModelHTTPError,
    OpenAISummarizer,
    UserError,
)


def test_contentsummarizer_is_abstract():
    with pytest.raises(TypeError):
        ContentSummarizer()


@patch("src.bookmarker.core.summarizers.Agent")
def test_summarizer_summarize(mock_agent_class):
    mock_agent_instance = Mock()
    mock_agent_instance.run_sync.return_value = Mock(output="This is a summary.")
    mock_agent_class.return_value = mock_agent_instance

    summarizer_instance = OpenAISummarizer("fake-key", "fake-model")
    output = summarizer_instance.summarize("Some article text")

    assert output == "This is a summary."
    summarizer_instance.agent.run_sync.assert_called_once_with("Some article text")


@pytest.mark.parametrize("bad_content", [None, "", "   "])
@patch("src.bookmarker.core.summarizers.Agent")
def test_summarize_invalid_content(mock_agent_class, bad_content):
    summarizer_instance = OpenAISummarizer("fake-key", "fake-model")

    with pytest.raises(InvalidContentError):
        summarizer_instance.summarize(bad_content)

    mock_agent_class.assert_called_once()
    mock_agent_class.return_value.assert_not_called()


@pytest.mark.parametrize("exc", [AgentRunError("boom"), UserError("bad input")])
@patch("src.bookmarker.core.summarizers.Agent")
def test_summarize_agent_errors(mock_agent_class, exc):
    mock_agent_instance = Mock()
    mock_agent_instance.run_sync.side_effect = exc
    mock_agent_class.return_value = mock_agent_instance

    summarizer_instance = OpenAISummarizer("fake-key", "fake-model")

    with pytest.raises(ContentSummaryError) as e:
        summarizer_instance.summarize("Some article text")

    assert "Error during content summarization" in str(e.value)


@patch("src.bookmarker.core.summarizers.Agent")
def test_summarize_agent_api_key_error(mock_agent_class):
    mock_agent_instance = Mock()
    mock_error = ModelHTTPError(401, "fake-model")
    mock_error.body = {"code": "invalid_api_key"}
    mock_agent_instance.run_sync.side_effect = mock_error
    mock_agent_class.return_value = mock_agent_instance

    summarizer_instance = OpenAISummarizer("bad-key", "fake-model")

    with pytest.raises(InvalidAPIKeyError) as e:
        summarizer_instance.summarize("Some article text")

    assert "Invalid OpenAI API key" in str(e.value)


@patch("src.bookmarker.core.summarizers.Agent")
def test_summarize_agent_http_error(mock_agent_class):
    mock_agent_instance = Mock()
    mock_error = ModelHTTPError(401, "fake-model")
    mock_error.body = {}
    mock_agent_instance.run_sync.side_effect = mock_error
    mock_agent_class.return_value = mock_agent_instance

    summarizer_instance = OpenAISummarizer("fake-key", "fake-model")

    with pytest.raises(ContentSummaryError) as e:
        summarizer_instance.summarize("Some article text")

    assert "OpenAI API HTTP error" in str(e.value)


@patch("src.bookmarker.core.summarizers.Agent")
def test_get_summarizer_returns_openai_instance(mock_agent_class, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "fake-key")
    monkeypatch.setenv("OPENAI_MODEL_NAME", "fake-model")

    summarizer = summarizers.get_summarizer()
    assert isinstance(summarizer, OpenAISummarizer)

    mock_agent_class.assert_called_once()
