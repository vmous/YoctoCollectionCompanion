"""Money helpers: currency validation and exchange-rate conversion.

Money is represented as integer **minor units** (cents) throughout the app, so
these helpers never introduce binary floating-point error into stored amounts.
This module is deliberately currency-agnostic: it validates ISO 4217 codes and
converts an amount from one currency to another given a rate, but it has no
notion of a "base" or "reporting" currency — that choice belongs to the
presentation layer. The rate itself is supplied by the caller (ultimately from
a date-keyed rate cache), not looked up here.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

import pycountry

# App-wide rounding policy for converting money to whole cents. HALF_UP is the
# familiar "round 0.5 away from zero" rule (39, not banker's-rounding 38), so
# converted amounts match hand calculation. Defined once here as the single
# source of truth rather than being configurable per call or per deployment —
# rounding is a fixed accounting policy, not an operational knob.
DEFAULT_ROUNDING = ROUND_HALF_UP


class UnknownCurrencyError(ValueError):
    """Raised when a currency code is not a recognised ISO 4217 code."""


def normalize_currency(code: str) -> str:
    """Validate an ISO 4217 currency code and return it normalised.

    Accepts a three-letter code in any case and with surrounding whitespace
    (e.g. ``" eur "``) and returns the canonical upper-case form (``"EUR"``).
    Raises :class:`UnknownCurrencyError` if the code is not a recognised ISO
    4217 alphabetic code.
    """
    candidate = code.strip().upper()
    if pycountry.currencies.get(alpha_3=candidate) is None:
        raise UnknownCurrencyError(f"Unknown ISO 4217 currency code: {code!r}")
    return candidate


def convert_cents(amount_cents: int, rate: float | Decimal) -> int:
    """Convert an integer-cents amount by ``rate``, returning integer cents.

    ``rate`` multiplies the source amount to yield the target amount (e.g. a
    GBP amount times a GBP->EUR rate gives EUR). The multiplication is done in
    :class:`~decimal.Decimal` to avoid binary floating-point drift, and the
    result is rounded to the nearest whole cent using :data:`DEFAULT_ROUNDING`.
    The caller supplies ``rate``; this module does not look rates up.
    """
    # str() the rate so a float like 0.9 becomes Decimal("0.9") rather than the
    # binary-float-tainted Decimal(0.9000000000000000222...).
    rate_decimal = rate if isinstance(rate, Decimal) else Decimal(str(rate))
    converted = Decimal(amount_cents) * rate_decimal
    return int(converted.quantize(Decimal("1"), rounding=DEFAULT_ROUNDING))
