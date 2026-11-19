# exceptions/configuration.py

from finance_cli.exceptions.base import PatrimoniaError


class ConfigurationError(PatrimoniaError):
    """Invalid or incomplete application configuration."""


class ResourceConfigurationError(ConfigurationError):
    """Invalid or incomplete resource configuration."""
