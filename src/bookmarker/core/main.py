from trafilatura import extract, fetch_url


def get_content(url):
    downloaded = fetch_url(url)
    if downloaded:
        return extract(
            downloaded,
            include_images=True,
            include_tables=True,
            include_links=True,
            output_format="markdown",
        )
    return None


if __name__ == "__main__":
    url = "https://kpdata.dev/blog/python-slicing/"
    content = get_content(url)
