from unittest.mock import patch

import pytest
import requests
import yfinance.exceptions as yf_exceptions

from finance_cli.adapters.web.yahoo_finance import YahooFinanceAdapter
from finance_cli.exceptions.providers import (
    ProviderConnectionError,
    ProviderDataError,
    ProviderSymbolError,
)


def test_fetch_equity_market_cap():
    """Une equity récupère sa capitalisation boursière."""

    info = {
        "quoteType": "EQUITY",
        "longName": "Apple Inc.",
        "currency": "USD",
        "marketCap": 3_000_000_000_000,
        "previousClose": 250.0,
    }

    with patch("finance_cli.adapters.web.yahoo_finance.yf.Ticker") as mock_ticker:
        mock_ticker.return_value.info = info

        scraped, raw = YahooFinanceAdapter().fetch("US0378331005", "AAPL")

    indicative = scraped.market_data.indicative

    assert indicative.market_cap == 3_000_000_000_000
    assert indicative.aum is None
    assert indicative.currency == "USD"
    assert scraped.agg_info.fund_currency is None
    assert raw == info


def test_fetch_etf_aum():
    """Un ETF récupère ses encours."""

    info = {
        "quoteType": "ETF",
        "longName": "iShares Core MSCI World",
        "currency": "EUR",
        "totalAssets": 50_000_000_000,
        "fundFamily": "BlackRock",
    }

    with patch("finance_cli.adapters.web.yahoo_finance.yf.Ticker") as mock_ticker:
        mock_ticker.return_value.info = info

        scraped, _ = YahooFinanceAdapter().fetch("IE00B4L5Y983", "IWDA.AS")

    indicative = scraped.market_data.indicative

    assert indicative.aum == 50_000_000_000
    assert indicative.market_cap is None
    assert indicative.currency == "EUR"
    assert scraped.agg_info.fund_currency == "EUR"
    assert scraped.agg_info.management_company == "BlackRock"


def test_fetch_currency_depends_on_quote_type():
    """La devise du fonds est réservée aux fonds et ETF."""

    equity_info = {
        "quoteType": "EQUITY",
        "shortName": "Example Equity",
        "currency": "USD",
    }

    with patch("finance_cli.adapters.web.yahoo_finance.yf.Ticker") as mock_ticker:
        mock_ticker.return_value.info = equity_info

        equity, _ = YahooFinanceAdapter().fetch("US0000000001", "TEST")

    assert equity.market_data.indicative.currency == "USD"
    assert equity.agg_info.fund_currency is None

    etf_info = {
        "quoteType": "ETF",
        "shortName": "Example ETF",
        "currency": "EUR",
    }

    with patch("finance_cli.adapters.web.yahoo_finance.yf.Ticker") as mock_ticker:
        mock_ticker.return_value.info = etf_info

        etf, _ = YahooFinanceAdapter().fetch("IE0000000001", "TEST.AS")

    assert etf.market_data.indicative.currency == "EUR"
    assert etf.agg_info.fund_currency == "EUR"


def test_fetch_translates_rate_limit_error():
    """Une limitation Yahoo est traduite en erreur de connexion fournisseur."""

    with patch(
        "finance_cli.adapters.web.yahoo_finance.yf.Ticker",
        side_effect=yf_exceptions.YFRateLimitError(),
    ):
        with pytest.raises(ProviderConnectionError):
            YahooFinanceAdapter().fetch("US0378331005", "AAPL")


def test_fetch_translates_missing_ticker_error():
    """Un ticker introuvable est traduit en erreur de symbole."""

    with patch(
        "finance_cli.adapters.web.yahoo_finance.yf.Ticker",
        side_effect=yf_exceptions.YFTickerMissingError("INVALID", "Ticker not found"),
    ):
        with pytest.raises(ProviderSymbolError):
            YahooFinanceAdapter().fetch("US0378331005", "INVALID")


def test_fetch_translates_missing_prices_error():
    """Des données de prix absentes sont traduites en erreur de données."""

    with patch(
        "finance_cli.adapters.web.yahoo_finance.yf.Ticker",
        side_effect=yf_exceptions.YFPricesMissingError(
            ticker="INVALID",
            debug_info="No price data found",
        ),
    ):
        with pytest.raises(ProviderDataError):
            YahooFinanceAdapter().fetch("US0378331005", "INVALID")


def test_fetch_translates_request_exception():
    """Une erreur réseau est traduite en erreur de connexion fournisseur."""

    with patch(
        "finance_cli.adapters.web.yahoo_finance.yf.Ticker",
        side_effect=requests.exceptions.ConnectionError("Connection failed"),
    ):
        with pytest.raises(ProviderConnectionError):
            YahooFinanceAdapter().fetch("US0378331005", "AAPL")


def test_fetch_translates_missing_timezone_error():
    """Un fuseau horaire manquant est traduit en erreur de données."""

    with patch(
        "finance_cli.adapters.web.yahoo_finance.yf.Ticker",
        side_effect=yf_exceptions.YFTzMissingError("AAPL"),
    ):
        with pytest.raises(ProviderDataError):
            YahooFinanceAdapter().fetch("US0378331005", "AAPL")


def test_fetch_translates_invalid_period_error():
    """Une période invalide est traduite en erreur de données."""

    with patch(
        "finance_cli.adapters.web.yahoo_finance.yf.Ticker",
        side_effect=yf_exceptions.YFInvalidPeriodError(
            "AAPL", "invalid", ["1d", "5d", "1mo"]
        ),
    ):
        with pytest.raises(ProviderDataError):
            YahooFinanceAdapter().fetch("US0378331005", "AAPL")


def test_fetch_translates_not_implemented_error():
    """Une fonctionnalité non prise en charge est traduite en erreur de données."""

    with patch(
        "finance_cli.adapters.web.yahoo_finance.yf.Ticker",
        side_effect=yf_exceptions.YFNotImplementedError("history"),
    ):
        with pytest.raises(ProviderDataError):
            YahooFinanceAdapter().fetch("US0378331005", "AAPL")
