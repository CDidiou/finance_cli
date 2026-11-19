from finance_cli.exceptions.base import PatrimoniaError


class ProviderError(PatrimoniaError):
    """Base exception for external data provider errors."""


class ProviderConnectionError(ProviderError):
    """The provider could not be reached."""


class ProviderDataError(ProviderError):
    """The provider returned invalid or unusable data."""


class ProviderSymbolError(ProviderError):
    """The requested symbol is unknown or unsupported."""
