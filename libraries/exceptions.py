

class ErrorInFetchingArticles(Exception):
    """Exception raised when an error occurs while fetching article data."""


class ErrorInDownloadException(Exception):
    """Exception subclass to track exceptions raised during downloading"""


class GeneralException(Exception):
    """Exception subclass to general exceptions"""


class ParserError(ValueError):
    """Exception subclass used for any failure to parse a datetime string."""
