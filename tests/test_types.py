"""Tests for the enumerated ``type`` vocabularies in :mod:`ycc.types`.

These are pure tests of the enum members themselves; how the models *persist*
these values is covered in ``test_models.py``.
"""

from ycc.types import ProductType, TransactionType


def test_transaction_type_values():
    assert TransactionType.BUY == "buy"
    assert TransactionType.SELL == "sell"


def test_product_type_values():
    assert ProductType.MTG == "mtg"
