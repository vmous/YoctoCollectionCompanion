"""Tests for the product-type spec table and its incoming-data checks."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from ycc.mtg import MtgAttributes, MtgCondition, MtgFinish
from ycc.product_spec import (
    PRODUCT_TYPE_SPECS,
    UnknownConditionError,
    validate_attributes,
    validate_condition,
)
from ycc.types import ProductType


def test_every_product_type_has_a_spec():
    # Drift guard: the spec table must cover exactly the defined product types,
    # so adding a ProductType member without a spec (or vice versa) fails here.
    assert set(ProductType) == set(PRODUCT_TYPE_SPECS)


def test_mtg_spec_wiring():
    spec = PRODUCT_TYPE_SPECS[ProductType.MTG]
    assert spec.attributes_model is MtgAttributes
    assert spec.condition_type is MtgCondition


class TestValidateAttributes:
    def _valid(self, **overrides):
        data = {
            "reprint_set_id": "plst",
            "original_set_id": "m20",
            "original_set_idx": "2",
            "language_code": "en-us",
        }
        data.update(overrides)
        return data

    def test_returns_normalised_dict(self):
        result = validate_attributes(ProductType.MTG, self._valid(original_set_id="M20"))
        assert isinstance(result, dict)
        assert result["original_set_id"] == "m20"  # lowercased by the model
        assert result["finish"] == MtgFinish.NONFOIL  # default applied

    def test_rejects_invalid(self):
        with pytest.raises(ValidationError):
            validate_attributes(ProductType.MTG, self._valid(finish="glossy"))

    def test_rejects_unknown_key(self):
        with pytest.raises(ValidationError):
            validate_attributes(ProductType.MTG, self._valid(rarity="rare"))


class TestValidateCondition:
    def test_accepts_valid_condition(self):
        assert validate_condition(ProductType.MTG, "Near Mint") == "Near Mint"

    def test_rejects_unknown_condition(self):
        with pytest.raises(UnknownConditionError):
            validate_condition(ProductType.MTG, "Pristine")

    def test_error_lists_allowed_values(self):
        with pytest.raises(UnknownConditionError, match="Near Mint"):
            validate_condition(ProductType.MTG, "Pristine")
