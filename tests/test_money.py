"""Tests for currency validation and exchange-rate conversion."""

from __future__ import annotations

from decimal import Decimal

import pytest

from ycc.money import UnknownCurrencyError, convert_cents, normalize_currency


class TestNormalizeCurrency:
    def test_accepts_canonical_code(self):
        assert normalize_currency("EUR") == "EUR"

    def test_uppercases_and_strips(self):
        assert normalize_currency(" eur ") == "EUR"
        assert normalize_currency("gbp") == "GBP"

    def test_various_real_codes(self):
        for code in ("USD", "JPY", "CHF", "SEK"):
            assert normalize_currency(code) == code

    def test_rejects_unknown_code(self):
        with pytest.raises(UnknownCurrencyError):
            normalize_currency("EURO")

    def test_rejects_empty(self):
        with pytest.raises(UnknownCurrencyError):
            normalize_currency("")

    def test_error_message_includes_original_input(self):
        with pytest.raises(UnknownCurrencyError, match="xyz"):
            normalize_currency("xyz")


class TestConvertCents:
    def test_identity_rate(self):
        assert convert_cents(15470, 1.0) == 15470

    def test_simple_rate(self):
        # 154.70 GBP at 0.90 -> 139.23 EUR
        assert convert_cents(15470, 0.90) == 13923

    def test_rounds_half_up(self):
        # 100 cents * 0.385 = 38.5 -> 39 (HALF_UP, not banker's 38)
        assert convert_cents(100, 0.385) == 39

    def test_rounds_half_up_below_midpoint(self):
        # 100 cents * 0.384 = 38.4 -> 38
        assert convert_cents(100, 0.384) == 38

    def test_accepts_decimal_rate(self):
        assert convert_cents(15470, Decimal("0.90")) == 13923

    def test_no_binary_float_drift(self):
        # A rate whose binary float is inexact must still round correctly:
        # 0.1 as a float is 0.1000000000000000055..., but str()-based Decimal
        # keeps it exact, so 1000 cents -> 100 cents, not 99 or 101.
        assert convert_cents(1000, 0.1) == 100

    def test_zero_amount(self):
        assert convert_cents(0, 0.90) == 0
