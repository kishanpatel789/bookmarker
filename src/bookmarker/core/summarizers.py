from abc import ABC, abstractmethod

from pydantic_ai import Agent
from pydantic_ai.exceptions import AgentRunError, ModelHTTPError, UserError
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from .config import get_config
from .exceptions import ContentSummaryError, InvalidAPIKeyError, InvalidContentError

SUMMARIZER_REGISTRY = {}


def register_summarizer(name: str):
    def decorator(cls):
        SUMMARIZER_REGISTRY[name] = cls
        return cls

    return decorator


class ContentSummarizer(ABC):
    @abstractmethod
    def summarize(self, content: str | None) -> str:
        """Summarize the given content and return the summary as a string."""


@register_summarizer("openai")
class OpenAISummarizer(ContentSummarizer):
    def __init__(self, api_key: str | None = None, model_name: str | None = None):
        config = get_config()
        if api_key is None:
            api_key = config("OPENAI_API_KEY")
        if model_name is None:
            model_name = config("OPENAI_MODEL_NAME", default="gpt-5-nano")
        model = OpenAIChatModel(model_name, provider=OpenAIProvider(api_key=api_key))
        self.agent = Agent(
            model,
            output_type=str,
            instructions=(
                """
                Summarize the article in a concise way. Write a short paragraph (3–4 sentences) that captures the key ideas,
                followed by 3–5 bullet points highlighting the most important takeaways. Avoid filler language.
                Write so that someone who didn’t read the article can understand the main points quickly. """
            ),
        )

    def summarize(self, content: str | None) -> str:
        if content is None or content.strip() == "":
            raise InvalidContentError(
                "Content is empty or None. Run fetcher first to get raw content."
            )
        try:
            result = self.agent.run_sync(content)
            return result.output
        except ModelHTTPError as e:
            if isinstance(e.body, dict):
                code = e.body.get("code")
                if code == "invalid_api_key":
                    raise InvalidAPIKeyError(f"Invalid OpenAI API key: {e}")
            raise ContentSummaryError(f"OpenAI API HTTP error: {e}")
        except (AgentRunError, UserError) as e:
            raise ContentSummaryError(f"Error during content summarization: {e}")


@register_summarizer("anthropic")
class AnthropicSummarizer(ContentSummarizer): ...


def get_summarizer() -> ContentSummarizer:
    config = get_config()
    backend = config("SUMMARIZER_BACKEND", default="openai")
    return SUMMARIZER_REGISTRY[backend]()
