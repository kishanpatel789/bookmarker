from abc import ABC, abstractmethod

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from .config import OPENAI_API_KEY, OPENAI_MODEL_NAME
from .exceptions import InvalidContentError


class ContentSummarizer(ABC):
    @abstractmethod
    def summarize(self, content: str) -> str:
        """Summarize the given content and return the summary as a string."""


class OpenAISummarizer(ContentSummarizer):
    def __init__(self, api_key: str, model_name: str):
        model = OpenAIChatModel(model_name, provider=OpenAIProvider(api_key=api_key))
        self.agent = Agent(
            model,
            deps_type=str,
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
        else:
            result = self.agent.run_sync(content)
            return result.output


def get_summarizer() -> ContentSummarizer:
    return OpenAISummarizer(api_key=OPENAI_API_KEY, model_name=OPENAI_MODEL_NAME)


if __name__ == "__main__":
    from .database import get_repo

    repo = get_repo()
    url = "https://kpdata.dev/blog/python-slicing/"

    artifact = repo.get_by_url(url)

    # result = summary_agent.run_sync(artifact.content_raw)
    # print(result.output)

    summarizer = OpenAISummarizer(api_key=OPENAI_API_KEY, model_name=OPENAI_MODEL_NAME)
    print(summarizer.summarize(artifact.content_raw))
