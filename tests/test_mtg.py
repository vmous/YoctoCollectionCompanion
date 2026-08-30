"""Tests for the MTG product type: attributes, finishes, and conditions."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from ycc.mtg import MtgAttributes, MtgCondition, MtgFinish


class TestMtgFinish:
    def test_values_match_scryfall(self):
        # Values mirror Scryfall's `finishes` vocabulary exactly.
        assert MtgFinish.NONFOIL == "nonfoil"
        assert MtgFinish.FOIL == "foil"
        assert MtgFinish.ETCHED == "etched"

    def test_exactly_three_finishes(self):
        assert {f.value for f in MtgFinish} == {"nonfoil", "foil", "etched"}


class TestMtgCondition:
    def test_cardmarket_seven_grades(self):
        assert [c.value for c in MtgCondition] == [
            "Mint",
            "Near Mint",
            "Excellent",
            "Good",
            "Light Played",
            "Played",
            "Poor",
        ]


class TestMtgAttributes:
    def _valid(self, **overrides):
        data = {
            "reprint_set_id": "plst",
            "original_set_id": "m20",
            "original_set_idx": "2",
            "language_code": "en-us",
        }
        data.update(overrides)
        return data

    def test_valid_attributes_parse(self):
        attrs = MtgAttributes.model_validate(self._valid())
        assert attrs.reprint_set_id == "plst"
        assert attrs.original_set_id == "m20"
        assert attrs.original_set_idx == "2"
        assert attrs.language_code == "en-us"

    def test_finish_defaults_to_nonfoil(self):
        assert MtgAttributes.model_validate(self._valid()).finish is MtgFinish.NONFOIL

    def test_finish_accepts_enum_value(self):
        attrs = MtgAttributes.model_validate(self._valid(finish="etched"))
        assert attrs.finish is MtgFinish.ETCHED

    def test_finish_rejects_unknown_value(self):
        with pytest.raises(ValidationError):
            MtgAttributes.model_validate(self._valid(finish="glossy"))

    def test_set_codes_are_lowercased(self):
        data = self._valid(original_set_id="M20", reprint_set_id="PLST")
        attrs = MtgAttributes.model_validate(data)
        assert attrs.original_set_id == "m20"
        assert attrs.reprint_set_id == "plst"

    def test_collector_number_keeps_suffix(self):
        # Collector numbers are strings and may carry suffixes.
        attrs = MtgAttributes.model_validate(self._valid(original_set_idx="2a"))
        assert attrs.original_set_idx == "2a"

    def test_empty_set_code_rejected(self):
        with pytest.raises(ValidationError):
            MtgAttributes.model_validate(self._valid(original_set_id="  "))

    def test_empty_collector_number_rejected(self):
        with pytest.raises(ValidationError):
            MtgAttributes.model_validate(self._valid(original_set_idx=""))

    def test_unknown_key_rejected(self):
        with pytest.raises(ValidationError):
            MtgAttributes.model_validate(self._valid(rarity="rare"))

    def test_missing_required_field_rejected(self):
        data = self._valid()
        del data["language_code"]
        with pytest.raises(ValidationError):
            MtgAttributes.model_validate(data)
