"""Magic: The Gathering product type: attribute schema and condition vocabulary.

This module holds the MTG-specific building blocks that validate a product's
generic ``attributes`` dict at the boundary. The database column stays a plain
JSON dict (so new product types need no schema change); :class:`MtgAttributes`
is what gives that dict a typed, validated shape when reading or writing an MTG
product. The type registry (a later sub-stage) wires this in per product type.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, field_validator


class MtgFinish(StrEnum):
    """How a card is finished. Part of a product's identity (foil != non-foil).

    Values mirror Scryfall's ``finishes`` vocabulary exactly, so no translation
    is needed when building Scryfall URLs or consuming its lookup API.
    """

    NONFOIL = "nonfoil"
    FOIL = "foil"
    ETCHED = "etched"


class MtgCondition(StrEnum):
    """Cardmarket's seven-grade condition scale, worst to best readability aside.

    The value is the canonical stored string; the member name is the grade's
    common abbreviation.
    """

    MT = "Mint"
    NM = "Near Mint"
    EX = "Excellent"
    GD = "Good"
    LP = "Light Played"
    PL = "Played"
    PO = "Poor"


class MtgAttributes(BaseModel):
    """Validated shape of an MTG product's ``attributes`` dict.

    Set codes are soft references to MTG set reference data (validated in the
    application layer, not here). ``original_set_idx`` is a string because
    collector numbers carry non-numeric suffixes (e.g. ``"2a"``, ``"★"``).
    ``reprint_set_id`` is the set the card physically lives in (e.g. ``"plst"``
    for The List); ``original_set_id`` is where it was first printed.
    """

    # Reject unknown keys so a typo'd attribute name fails loudly rather than
    # being silently dropped.
    model_config = ConfigDict(extra="forbid")

    reprint_set_id: str
    original_set_id: str
    original_set_idx: str
    language_code: str
    finish: MtgFinish = MtgFinish.NONFOIL

    @field_validator("reprint_set_id", "original_set_id")
    @classmethod
    def _normalize_set_code(cls, value: str) -> str:
        """Store set codes in Scryfall-canonical lowercase (e.g. ``"m20"``)."""
        code = value.strip().lower()
        if not code:
            raise ValueError("set code must not be empty")
        return code

    @field_validator("original_set_idx", "language_code")
    @classmethod
    def _require_non_empty(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be empty")
        return stripped
