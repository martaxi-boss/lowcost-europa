"""Small provider-independent validators for official Google Search Console metrics.

No third-party analytics access, credentials, cookies, or visitor-level data.
"""

from decimal import Decimal, InvalidOperation


EXPECTED_PROPERTY = "sc-domain:lowcost-europa.eu"


class SearchConsoleReportError(Exception):
    pass


class SearchConsoleNotConfigured(SearchConsoleReportError):
    pass


class SearchConsoleAwaitingData(SearchConsoleReportError):
    """A valid official response has no report rows; do not invent zero counts."""


def _nonnegative_int(value, *, name):
    if isinstance(value, bool) or value is None:
        raise SearchConsoleReportError("invalid_" + name)
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise SearchConsoleReportError("invalid_" + name) from None
    if not number.is_finite() or number < 0 or number != number.to_integral_value():
        raise SearchConsoleReportError("invalid_" + name)
    return int(number)


def _average_position(value, *, impressions):
    if impressions == 0:
        return None
    if isinstance(value, bool) or value is None:
        raise SearchConsoleReportError("missing_position")
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise SearchConsoleReportError("invalid_position") from None
    if not number.is_finite() or number <= 0 or number > 100000:
        raise SearchConsoleReportError("invalid_position")
    return str(number.quantize(Decimal("0.01")))
