from abc import ABC, abstractmethod

from decouple import config
from pydantic_ai import Agent
from pydantic_ai.exceptions import AgentRunError, UserError
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from .exceptions import ContentSummaryError, InvalidContentError

SUMMARIZER_REGISTRY = {}


def register_summarizer(name: str):
    def decorator(cls):
        SUMMARIZER_REGISTRY[name] = cls
        return cls

    return decorator


class ContentSummarizer(ABC):
    @abstractmethod
    def summarize(self, content: str) -> str:
        """Summarize the given content and return the summary as a string."""


@register_summarizer("openai")
class OpenAISummarizer(ContentSummarizer):
    def __init__(self, api_key: str | None = None, model_name: str | None = None):
        if api_key is None:
            api_key = config("OPENAI_API_KEY")
        if model_name is None:
            model_name = config("OPENAI_MODEL_NAME")
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
        except (AgentRunError, UserError) as e:
            raise ContentSummaryError(f"Error during content summarization: {e}")


@register_summarizer("anthropic")
class AnthropicSummarizer(ContentSummarizer): ...


def get_summarizer() -> ContentSummarizer:
    backend = config("SUMMARIZER_BACKEND", default="openai")
    return SUMMARIZER_REGISTRY[backend]()
