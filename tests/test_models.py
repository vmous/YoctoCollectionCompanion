"""Tests for the data model.

These build a throwaway in-memory SQLite database per test, so they verify
that the tables create, relationships resolve, and the derived-state links
(held vs. disposed, known vs. unknown provenance) behave as designed — without
any application wiring.
"""

from __future__ import annotations

from datetime import date

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from ycc.models import Copy, Counterparty, Product, Transaction
from ycc.types import ProductType, TransactionType


@pytest.fixture
def session():
    """A session against a fresh in-memory SQLite database."""
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


def test_all_tables_create(session):
    # If the metadata is self-consistent, every table exists and is queryable.
    assert session.exec(select(Counterparty)).all() == []
    assert session.exec(select(Transaction)).all() == []
    assert session.exec(select(Product)).all() == []
    assert session.exec(select(Copy)).all() == []


def test_type_columns_store_lowercase_value(session):
    # The enum-typed `type` columns must persist the enum *value* ("buy",
    # "mtg"), not the member name ("BUY", "MTG"). This guards against a stray
    # drop of `sa_type=String`, which would revert to sa.Enum and store names.
    txn = Transaction(type=TransactionType.BUY, date=date(2026, 8, 18))
    product = Product(type=ProductType.MTG, title="Lightning Bolt")
    session.add_all([txn, product])
    session.commit()

    conn = session.connection()
    # "transaction" is a SQL reserved word, so the table name must be quoted.
    raw_txn = conn.exec_driver_sql(
        'SELECT type FROM "transaction" WHERE id = ?', (txn.id,)
    ).scalar()
    raw_product = conn.exec_driver_sql(
        "SELECT type FROM product WHERE id = ?", (product.id,)
    ).scalar()
    assert raw_txn == "buy"
    assert raw_product == "mtg"


def test_counterparty_transaction_relationship(session):
    shop = Counterparty(name="Cardmarket")
    txn = Transaction(type=TransactionType.BUY, date=date(2026, 8, 18), counterparty=shop)
    session.add(txn)
    session.commit()
    session.refresh(shop)

    assert txn.counterparty is shop
    assert shop.transactions == [txn]


def test_product_attributes_roundtrip_json(session):
    # Type-specific fields live in the JSON attributes column and survive a
    # write/read cycle unchanged.
    product = Product(
        type=ProductType.MTG,
        title="Ajani, Strength of the Pride",
        attributes={
            "reprint_set_id": "plst",
            "original_set_id": "m20",
            "original_set_idx": "2",
            "language_code": "en-us",
            "is_foil": False,
        },
    )
    session.add(product)
    session.commit()
    session.refresh(product)

    fetched = session.get(Product, product.id)
    assert fetched.attributes["original_set_id"] == "m20"
    assert fetched.attributes["is_foil"] is False


def test_copy_acquisition_and_disposal_links(session):
    # A copy points at the buy that brought it in and the sell that took it out,
    # via two distinct foreign keys to Transaction.
    product = Product(type=ProductType.MTG, title="Moltensteel Dragon")
    buy = Transaction(type=TransactionType.BUY, date=date(2026, 8, 18), currency="EUR")
    sell = Transaction(type=TransactionType.SELL, date=date(2026, 9, 1), currency="EUR")
    copy = Copy(
        product=product,
        acquired_in=buy,
        acquired_amount_cents=75,
        disposed_in=sell,
        disposed_amount_cents=200,
    )
    session.add(copy)
    session.commit()
    session.refresh(buy)
    session.refresh(sell)

    assert copy.acquired_in is buy
    assert copy.disposed_in is sell
    assert buy.copies_acquired == [copy]
    assert sell.copies_disposed == [copy]
    assert buy.copies_disposed == []  # the buy did not dispose of anything


def test_held_copy_has_no_disposal(session):
    # "Held" is derived: disposed_in_id is null.
    product = Product(type=ProductType.MTG, title="Chancellor of the Forge")
    buy = Transaction(type=TransactionType.BUY, date=date(2026, 8, 18))
    held = Copy(product=product, acquired_in=buy, acquired_amount_cents=30)
    session.add(held)
    session.commit()

    still_held = session.exec(select(Copy).where(Copy.disposed_in_id.is_(None))).all()
    assert still_held == [held]


def test_unknown_provenance_copy_has_no_acquisition(session):
    # A copy owned without a recorded purchase (gift/pull) has no acquisition.
    product = Product(type=ProductType.MTG, title="Black Lotus")
    orphan = Copy(product=product)
    session.add(orphan)
    session.commit()

    assert orphan.acquired_in_id is None
    assert orphan.acquired_in is None
    unknown = session.exec(select(Copy).where(Copy.acquired_in_id.is_(None))).all()
    assert unknown == [orphan]


def test_product_copies_backref(session):
    # Multiple physical copies of one product (e.g. a playset) share one Product.
    product = Product(type=ProductType.MTG, title="Lightning Bolt")
    buy = Transaction(type=TransactionType.BUY, date=date(2026, 8, 18))
    copies = [Copy(product=product, acquired_in=buy, acquired_amount_cents=100) for _ in range(4)]
    session.add_all(copies)
    session.commit()
    session.refresh(product)

    assert len(product.copies) == 4
