

class ErrorInFetchingArticles(Exception):
    ...


class ErrorInDownloadException(Exception):
    ...


class NoMatchFoundError(ValueError):
    ...

class GeneralException(ValueError):
    ...