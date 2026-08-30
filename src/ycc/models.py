"""Database models for the collection catalog and cost ledger.

These four tables model a personal collection as a two-sided ledger of what is
owned and what it cost. A :class:`Product` is a distinct collectible — a
specific card, game, or comic — while a :class:`Copy` is one physical instance
of it; many copies can share a product, so duplicates and playsets roll up
under a single catalogue entry. A :class:`Transaction` is a purchase or a sale,
made with a :class:`Counterparty` (a shop or platform).

The ledger emerges from how each :class:`Copy` connects to transactions: it
links to the one that acquired it and, once sold, to the one that disposed of
it. From those links the collection answers its questions — what is currently
held (copies not yet disposed), what has been sold, and what a copy of unknown
provenance (owned but never purchased) is — while a transaction's price,
shipping, tax, and fees let a per-copy cost be derived. Rolling copies up under
products, and transactions up under counterparties, totals holdings and
spending by collectible, by shop, or across the whole collection.

Entity relationships. Each connector is one foreign key: the ``1`` end is the
referenced table, the ``*`` end holds the named foreign-key column::

              ┌──────────────┐
              │   Product    │
              └──────┬───────┘
                     │ 1
                     │ product_id
                     │ *
              ┌──────┴───────┐
              │     Copy     │
              └───┬──────┬───┘
                * │      │ *
   acquired_in_id │      │ disposed_in_id
                1 │      │ 1
              ┌───┴──────┴───┐
              │ Transaction  │
              └──────┬───────┘
                     │ *
                     │ counterparty_id
                     │ 1
              ┌──────┴───────┐
              │ Counterparty │
              └──────────────┘

Type-specific reference tables (e.g. a Magic: The Gathering set lookup) arrive
with the product-type work that first populates and reads them, keyed softly by
code from a product's ``attributes``.
"""

from datetime import date

from sqlalchemy import JSON, String
from sqlmodel import Field, Relationship, SQLModel

from ycc.types import ProductType, TransactionType


class Counterparty(SQLModel, table=True):
    """A shop or platform a transaction is made with (e.g. eBay, Cardmarket)."""

    id: int | None = Field(default=None, primary_key=True)
    name: str
    url: str | None = None
    notes: str | None = None

    transactions: list["Transaction"] = Relationship(back_populates="counterparty")


class Transaction(SQLModel, table=True):
    """A money event: a purchase (``buy``) or a sale (``sell``).

    Shipping, tax, and fees are stored as separate amounts so that a per-item
    landed cost can be derived by allocating them across the transaction's
    copies. All monetary fields are integer minor units (cents) in ``currency``
    to avoid floating-point drift; ``currency`` follows ISO 4217. Conversion to
    a reporting currency is done at presentation time from a rate cache, not
    stored on the transaction.
    """

    id: int | None = Field(default=None, primary_key=True)
    # Do NOT switch to sa.Enum: it would store member names and couple DDL to
    # the enum's contents. Reads return a plain str, so compare against the
    # constants (type == TransactionType.BUY), do NOT use isinstance. Value
    # validation lives in the service layer.
    type: TransactionType = Field(sa_type=String)
    date: date
    counterparty_id: int | None = Field(default=None, foreign_key="counterparty.id")

    # The currency the transaction was made in (ISO 4217). This and the date
    # are immutable facts; the exchange rate to any reporting currency is
    # derived at presentation time from a (date, currency) rate cache, not
    # stored here.
    currency: str = "EUR"  # ISO 4217

    shipping_cents: int = 0
    tax_cents: int = 0
    fees_cents: int = 0

    order_reference: str | None = None  # the platform's order number
    order_url: str | None = None  # deep link back to the order on the platform
    notes: str | None = None

    counterparty: Counterparty | None = Relationship(back_populates="transactions")

    # Copies this transaction brought in (for a buy) or took out (for a sell).
    # Both links point at Transaction, so the foreign key to use must be named
    # explicitly to disambiguate the two relationships.
    copies_acquired: list["Copy"] = Relationship(
        back_populates="acquired_in",
        sa_relationship_kwargs={"foreign_keys": "Copy.acquired_in_id"},
    )
    copies_disposed: list["Copy"] = Relationship(
        back_populates="disposed_in",
        sa_relationship_kwargs={"foreign_keys": "Copy.disposed_in_id"},
    )


class Product(SQLModel, table=True):
    """A distinct collectible — one row per distinct printing.

    Identity is per-printing: a foil and a non-foil of the same card are two
    products. Type-specific attributes (set, rarity, finish, ...) live in the
    JSON ``attributes`` column rather than as dedicated columns, so a new
    product type needs no schema change. ``current_value_cents`` and
    ``value_as_of`` are reserved for future market-value tracking and unused
    for now.
    """

    id: int | None = Field(default=None, primary_key=True)
    # Enum-typed for IDE support, backed by a plain String column (see the note
    # on Transaction.type). The set of types stays open: new members are added
    # to ProductType and, in a later stage, the registry keyed by it. Reads
    # return a plain str; compare against ProductType constants, not isinstance.
    type: ProductType = Field(sa_type=String)
    title: str
    attributes: dict = Field(default_factory=dict, sa_type=JSON)

    external_id: str | None = None  # e.g. a Scryfall UUID (reserved for lookups)
    image_url: str | None = None

    current_value_cents: int | None = None  # reserved: market-value tracking
    value_as_of: date | None = None

    copies: list["Copy"] = Relationship(back_populates="product")


class Copy(SQLModel, table=True):
    """A single physical copy of a product that you own or have owned.

    A copy is *held* while ``disposed_in_id`` is null. A copy with no
    ``acquired_in`` link is owned but of unknown provenance (e.g. a gift or a
    pack pull). Per-copy state (condition, grade, ...) lives here; ``attributes``
    holds type-specific per-instance details.

    Collection states are derived from these links by query, never stored as
    columns: a copy is held when ``disposed_in_id`` is null, and a product is
    *in the collection* when it has at least one held copy.
    """

    id: int | None = Field(default=None, primary_key=True)
    product_id: int | None = Field(default=None, foreign_key="product.id")

    condition: str | None = None
    attributes: dict = Field(default_factory=dict, sa_type=JSON)
    notes: str | None = None

    acquired_in_id: int | None = Field(default=None, foreign_key="transaction.id")
    acquired_amount_cents: int | None = None  # unit price in the buy transaction's currency

    disposed_in_id: int | None = Field(default=None, foreign_key="transaction.id")
    disposed_amount_cents: int | None = None  # proceeds in the sell transaction's currency

    product: Product | None = Relationship(back_populates="copies")
    acquired_in: Transaction | None = Relationship(
        back_populates="copies_acquired",
        sa_relationship_kwargs={"foreign_keys": "Copy.acquired_in_id"},
    )
    disposed_in: Transaction | None = Relationship(
        back_populates="copies_disposed",
        sa_relationship_kwargs={"foreign_keys": "Copy.disposed_in_id"},
    )
