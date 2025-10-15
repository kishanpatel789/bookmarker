from unittest.mock import Mock, patch

import pytest

from src.bookmarker.cli.helpers import app_callback


@pytest.mark.focus
@patch("src.bookmarker.cli.helpers.get_repo")
def test_app_callback_runtime_error(mock_get_repo):
    mock_get_repo.side_effect = RuntimeError()
    mock_ctx = Mock()
    mock_ctx.invoked_subcommand == "not init"

    with pytest.raises(RuntimeError):
        app_callback(mock_ctx)
