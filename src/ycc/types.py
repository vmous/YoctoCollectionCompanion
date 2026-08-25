"""Enumerated value vocabularies for the model's ``type`` discriminators.

This is a leaf module: it imports nothing from :mod:`ycc.models`, so the models
can import these enums without risking a circular import. It holds *what values
exist*; a later stage adds a registry (keyed by :class:`ProductType`) that owns
*what each product type does* (attribute schema, form template, condition
vocabulary, external-lookup source).
"""

from enum import StrEnum


class TransactionType(StrEnum):
    """Canonical values for :attr:`ycc.models.Transaction.type`.

    A closed set: a transaction is either a purchase or a sale. Stored as its
    lowercase value; these members are the constants callers compare against
    (e.g. ``type == TransactionType.BUY``).
    """

    BUY = "buy"
    SELL = "sell"


class ProductType(StrEnum):
    """Canonical values for :attr:`ycc.models.Product.type`.

    Stored as its lowercase value (e.g. ``"mtg"``) in a plain string column.
    Only the types the app currently handles are listed; more are added as each
    is built out. ``OTHER`` is the freeform escape hatch — its open-endedness
    lives in that type's attribute schema, not in this discriminator.
    """

    MTG = "mtg"
    OTHER = "other"
