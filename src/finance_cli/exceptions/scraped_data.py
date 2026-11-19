from finance_cli.exceptions.base import PatrimoniaError


class ScrapedDataError(PatrimoniaError):
    """Base exception for scraped data errors."""


class ScrapedDataContentError(ScrapedDataError):
    """The scraped data document is invalid."""


class ScrapedDataStorageError(ScrapedDataError):
    """A scraped data storage operation failed."""
