from abc import ABC, abstractclassmethod

from trafilatura import extract, fetch_url

from .exceptions import ContentFetchError


class ContentFetcher(ABC):
    @abstractclassmethod
    def fetch(self, url: str) -> str:
        """Fetch content from url and return parsed content as string."""


class TrafilaturaFetcher(ContentFetcher):
    def fetch(self, url: str) -> str:
        downloaded = fetch_url(url)
        if downloaded is None:
            raise ContentFetchError(f"Failed to fetch content from URL: {url}")

        return extract(
            downloaded,
            include_images=True,
            include_tables=True,
            include_links=True,
            output_format="markdown",
        )


class YouTubeFetcher(ContentFetcher):
    def fetch(self, url: str) -> str: ...
