class ArtifactNotFoundError(Exception):
    pass


class ContentFetchError(Exception):
    pass


class InvalidContentError(Exception):
    pass


class ContentSummaryError(Exception):
    pass


class ContentSummaryExistsWarning(Exception):
    pass


class InvalidAPIKeyError(Exception):
    pass
