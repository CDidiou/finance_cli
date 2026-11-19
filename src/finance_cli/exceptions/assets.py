from finance_cli.exceptions.base import PatrimoniaError


class AssetError(PatrimoniaError):
    """Base exception for asset-related errors."""


class AssetNotFoundError(AssetError):
    """The requested asset does not exist."""


class AssetAmbiguousError(AssetError):
    """Several assets match the requested identifier."""


class AssetStorageError(AssetError):
    """An asset storage operation failed."""


class AssetContentError(AssetError):
    """Invalid or inconsistent asset catalogue content."""
