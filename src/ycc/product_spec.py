"""Per-product-type specifications, and checks for incoming data.

Each supported product type has a :class:`ProductSpec` describing what varies
by type: the Pydantic model that validates a product's ``attributes`` (properties
of the *printing*) and the condition vocabulary allowed on a *copy* (the
physical item's state). These two live on different tables — ``Product`` and
``Copy`` — so they are siblings on the spec, not nested.

``PRODUCT_TYPE_SPECS`` is a static table (not a dynamic registry) keyed by
:class:`~ycc.types.ProductType`; it is the single source of "which types exist
and how each behaves". Because the database columns store this data loosely (a
plain JSON dict for attributes, a plain string for condition), the helpers
below are the place that checks incoming attribute dicts and condition strings
*before* they are saved — so invalid data never reaches the database.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from pydantic import BaseModel

from ycc.mtg import MtgAttributes, MtgCondition
from ycc.types import ProductType


@dataclass(frozen=True)
class ProductSpec:
    """The per-type behaviour of one product type.

    ``attributes_model`` validates ``Product.attributes`` for this type;
    ``condition_type`` is the enum of allowed ``Copy.condition`` values.
    """

    attributes_model: type[BaseModel]
    condition_type: type[StrEnum]


PRODUCT_TYPE_SPECS: dict[ProductType, ProductSpec] = {
    ProductType.MTG: ProductSpec(
        attributes_model=MtgAttributes,
        condition_type=MtgCondition,
    ),
}


class UnknownConditionError(ValueError):
    """Raised when a condition is not in a product type's vocabulary."""


def validate_attributes(product_type: ProductType, data: dict) -> dict:
    """Validate a raw ``attributes`` dict for ``product_type``.

    Runs the dict through the type's Pydantic model and returns the normalised
    dict ready to store on ``Product.attributes``. Raises
    :class:`pydantic.ValidationError` if the data does not fit the schema.
    """
    model = PRODUCT_TYPE_SPECS[product_type].attributes_model
    return model.model_validate(data).model_dump()


def validate_condition(product_type: ProductType, condition: str) -> str:
    """Validate a copy ``condition`` against ``product_type``'s vocabulary.

    Returns the canonical condition value. Raises
    :class:`UnknownConditionError` if the value is not part of the type's
    condition enum.
    """
    condition_type = PRODUCT_TYPE_SPECS[product_type].condition_type
    try:
        return condition_type(condition).value
    except ValueError as exc:
        allowed = ", ".join(c.value for c in condition_type)
        raise UnknownConditionError(
            f"{condition!r} is not a valid {product_type} condition; expected one of: {allowed}"
        ) from exc
