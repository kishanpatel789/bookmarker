from decouple import config
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

OPENAI_API_KEY = config("OPENAI_API_KEY")


model = OpenAIChatModel("gpt-5-nano", provider=OpenAIProvider(api_key=OPENAI_API_KEY))

summary_agent = Agent(
    model,
    deps_type=str,
    output_type=str,
    instructions=(
        """
Summarize the article in a concise way. Write a short paragraph (3–4 sentences) that captures the key ideas, followed by 3–5 bullet points highlighting the most important takeaways. Avoid filler language. Write so that someone who didn’t read the article can understand the main points quickly. """
    ),
)


if __name__ == "__main__":
    from .database import get_repo

    repo = get_repo()
    url = "https://kpdata.dev/blog/python-slicing/"

    artifact = repo.get_by_url(url)

    result = summary_agent.run_sync(artifact.content_raw)
    print(result.output)
