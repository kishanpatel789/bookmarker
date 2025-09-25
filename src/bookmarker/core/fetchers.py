from abc import ABC, abstractmethod

from trafilatura import extract, fetch_url

from .exceptions import ContentFetchError


class ContentFetcher(ABC):
    @abstractmethod
    def fetch(self, url: str) -> str:
        """Fetch content from url and return parsed content as string."""


class TrafilaturaFetcher(ContentFetcher):
    def get_content(self, url: str) -> str:
        downloaded = fetch_url(url)
        if downloaded is None:
            raise ContentFetchError(f"Failed to fetch content from URL: {url}")

    def parse_content(self, content: str) -> str:
        return extract(
            content,
            include_images=True,
            include_tables=True,
            include_links=True,
            output_format="markdown",
        )

    def fetch(self, url: str) -> str:
        content = self.get_content(url)
        return self.parse_content(content)


class YouTubeFetcher(ContentFetcher):
    def fetch(self, url: str) -> str: ...
