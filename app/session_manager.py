"""
session_manager.py — AgroPrecios Bot
In-memory session state machine for the WhatsApp conversation flow.

Flow:
    start → awaiting_city → awaiting_product → done → (loop back to awaiting_product or start)

Session structure per user (keyed by wa_id / WhatsApp phone number):
    {
        "step":         str,        # current state in the flow
        "city_id":      int | None, # set after user picks a city
        "city_name":    str | None, # human-readable city name for messages
        "product_id":   int | None, # set after user picks a product
        "product_name": str | None, # human-readable product name for messages
    }
"""

from __future__ import annotations
from typing import Any

# ---------------------------------------------------------------------------
# Valid steps — single source of truth
# ---------------------------------------------------------------------------
STEPS = {
    "start",
    "awaiting_city",
    "awaiting_product",
    "done",
}

# ---------------------------------------------------------------------------
# In-memory store  (wa_id → session dict)
# ---------------------------------------------------------------------------
_sessions: dict[str, dict[str, Any]] = {}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _default_session() -> dict[str, Any]:
    """Returns a fresh session at the 'start' step."""
    return {
        "step":         "start",
        "city_id":      None,
        "city_name":    None,
        "product_id":   None,
        "product_name": None,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_session(wa_id: str) -> dict[str, Any]:
    """
    Returns the session for wa_id, creating a fresh one if it doesn't exist.
    Always returns a dict — never None.
    """
    if wa_id not in _sessions:
        _sessions[wa_id] = _default_session()
    return _sessions[wa_id]


def set_step(wa_id: str, step: str, **data: Any) -> dict[str, Any]:
    """
    Transitions wa_id to a new step and optionally stores extra data
    (e.g. city_id, city_name, product_id, product_name).

    Raises ValueError for unknown steps so bugs surface immediately.
    Returns the updated session dict.
    """
    if step not in STEPS:
        raise ValueError(
            f"Unknown step '{step}'. Valid steps are: {sorted(STEPS)}"
        )

    session = get_session(wa_id)
    session["step"] = step

    # Merge any extra keyword arguments (city_id, city_name, …) into session
    for key, value in data.items():
        if key not in session:
            raise KeyError(
                f"'{key}' is not a recognised session field. "
                f"Allowed: {list(session.keys())}"
            )
        session[key] = value

    _sessions[wa_id] = session
    return session


def reset_session(wa_id: str) -> dict[str, Any]:
    """
    Wipes all state for wa_id and returns them to 'start'.
    Equivalent to the user sending 'Inicio'.
    """
    _sessions[wa_id] = _default_session()
    return _sessions[wa_id]


# ---------------------------------------------------------------------------
# Transition helpers (what the webhook handler will call)
# ---------------------------------------------------------------------------

def transition_to_city(wa_id: str) -> dict[str, Any]:
    """Bot has sent the city list — waiting for user to pick."""
    return set_step(wa_id, "awaiting_city")


def transition_to_product(wa_id: str, city_id: int, city_name: str) -> dict[str, Any]:
    """User picked a city — bot has sent the product list."""
    return set_step(
        wa_id, "awaiting_product",
        city_id=city_id,
        city_name=city_name,
        product_id=None,      # clear any previous product
        product_name=None,
    )


def transition_to_done(wa_id: str, product_id: int, product_name: str) -> dict[str, Any]:
    """User picked a product — bot has sent the price card."""
    return set_step(
        wa_id, "done",
        product_id=product_id,
        product_name=product_name,
    )


def next_step(session: dict[str, Any]) -> str:
    """
    Given the current session, returns the *expected next* step.
    Useful for the webhook handler to decide what to do with an incoming message.

    Mapping:
        start             → awaiting_city      (send greeting + city list)
        awaiting_city     → awaiting_product   (user replied with a city)
        awaiting_product  → done               (user replied with a product)
        done              → awaiting_product   (user tapped "Otro producto")
                                               reset_session() handles "Inicio"
    """
    mapping = {
        "start":            "awaiting_city",
        "awaiting_city":    "awaiting_product",
        "awaiting_product": "done",
        "done":             "awaiting_product",
    }
    return mapping[session["step"]]
