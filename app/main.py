"""
main.py — AgroPrecios WhatsApp Bot
-----------------------------------
Wires together:
  • db_queries.py       (Step 3 — SQLite)
  • session_manager.py  (Step 4 — state machine)
  • sender.py           (Step 5 — Meta API)

Conversation flow:
  start
    └─► send greeting + city list  → set awaiting_city
  awaiting_city
    └─► user picks city            → send product list  → set awaiting_product
  awaiting_product
    └─► user picks product         → send price card   → set done
  done
    └─► "btn_otro"   → send product list (same city)  → stay awaiting_product
    └─► "btn_inicio" → reset session                   → send greeting + city list → set awaiting_city
  (any step) free text "hola" / unknown → nudge back to current step
"""

from __future__ import annotations

import logging
import os
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

import db_queries as db
import session_manager as sm
import sender

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

# ── App & config ──────────────────────────────────────────────────────────────
app = FastAPI(title="AgroPrecios Bot")

VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "agroprecios_verify_2025")

# ── Startup migration ─────────────────────────────────────────────────────────
@app.on_event("startup")
def on_startup() -> None:
    db.run_migrations()
    logger.info("DB migrations complete. Bot ready.")


# ── GET /webhook — Meta verification handshake ────────────────────────────────
@app.get("/webhook")
def verify_webhook(
    hub_mode:         str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge:    str = Query(None, alias="hub.challenge"),
):
    logger.info("Webhook verification request received.")
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        logger.info("Webhook verified OK.")
        return PlainTextResponse(content=hub_challenge, status_code=200)
    logger.warning(
        "Verification FAILED. Expected '%s', got '%s'.", VERIFY_TOKEN, hub_verify_token
    )
    raise HTTPException(status_code=403, detail="Verification failed")


# ── POST /webhook — receive incoming WhatsApp messages ────────────────────────
@app.post("/webhook")
async def receive_webhook(request: Request):
    """
    Meta sends all events here. We:
      1. Parse the payload to find the message (if any).
      2. Ignore non-message events (status updates, etc.) silently.
      3. Route to the correct handler based on session step.
    """
    body = await request.json()
    logger.debug("Incoming payload: %s", body)

    # ── Parse Meta's envelope ─────────────────────────────────────────────────
    try:
        entry   = body["entry"][0]
        changes = entry["changes"][0]["value"]

        # Ignore delivery/read receipts — they have no "messages" key
        if "messages" not in changes:
            return {"status": "ignored"}

        message = changes["messages"][0]
        wa_id   = message["from"]            # sender's WhatsApp number
        msg_type = message.get("type", "")  # "text", "interactive", etc.

    except (KeyError, IndexError):
        logger.warning("Unrecognised payload structure — ignoring.")
        return {"status": "ignored"}

    # ── Extract what the user actually sent ───────────────────────────────────
    selected_id    = None   # reply_id from a list/button tap
    selected_title = None   # human label of what they tapped
    free_text      = None   # raw text if they typed instead of tapping

    if msg_type == "interactive":
        interactive = message.get("interactive", {})
        itype = interactive.get("type")

        if itype == "list_reply":
            reply         = interactive["list_reply"]
            selected_id   = reply["id"]
            selected_title = reply.get("title", "")

        elif itype == "button_reply":
            reply         = interactive["button_reply"]
            selected_id   = reply["id"]
            selected_title = reply.get("title", "")

    elif msg_type == "text":
        free_text = message.get("text", {}).get("body", "").strip()

    logger.info(
        "Message from %s | type=%s | id=%s | text=%s",
        wa_id, msg_type, selected_id, free_text or selected_title,
    )

    # ── Route to the right handler ────────────────────────────────────────────
    session = sm.get_session(wa_id)
    step    = session["step"]

    # "Inicio" button resets from any step
    if selected_id == "btn_inicio":
        sm.reset_session(wa_id)
        _send_greeting_and_cities(wa_id)
        return {"status": "ok"}

    if step == "start":
        _handle_start(wa_id)

    elif step == "awaiting_city":
        _handle_awaiting_city(wa_id, selected_id, selected_title, free_text)

    elif step == "awaiting_product":
        _handle_awaiting_product(wa_id, selected_id, selected_title, free_text, session)

    elif step == "done":
        _handle_done(wa_id, selected_id, session)

    return {"status": "ok"}


# ── Step handlers ─────────────────────────────────────────────────────────────

def _handle_start(wa_id: str) -> None:
    """First contact — send greeting and city list."""
    _send_greeting_and_cities(wa_id)


def _handle_awaiting_city(
    wa_id:         str,
    selected_id:   str | None,
    selected_title: str | None,
    free_text:     str | None,
) -> None:
    """User should be tapping a city from the list."""

    if selected_id is None:
        # They typed something instead of tapping — nudge them
        sender.send_text(
            wa_id,
            "👆 Por favor selecciona una ciudad de la lista de opciones."
        )
        return

    # selected_id is something like "city_3"
    city_id = _parse_int_id(selected_id, prefix="city_")
    if city_id is None:
        sender.send_text(wa_id, "No pude identificar la ciudad. Intenta de nuevo.")
        return

    city_name = selected_title or f"Ciudad {city_id}"
    sm.transition_to_product(wa_id, city_id=city_id, city_name=city_name)
    _send_product_list(wa_id, city_name)


def _handle_awaiting_product(
    wa_id:          str,
    selected_id:    str | None,
    selected_title: str | None,
    free_text:      str | None,
    session:        dict,
) -> None:
    """User should be tapping a product from the list."""

    if selected_id is None:
        sender.send_text(
            wa_id,
            "👆 Por favor selecciona un producto de la lista de opciones."
        )
        return

    product_id = _parse_int_id(selected_id, prefix="prod_")
    if product_id is None:
        sender.send_text(wa_id, "No pude identificar el producto. Intenta de nuevo.")
        return

    product_name = selected_title or f"Producto {product_id}"
    city_id      = session["city_id"]
    city_name    = session["city_name"]

    sm.transition_to_done(wa_id, product_id=product_id, product_name=product_name)
    _send_price_card(wa_id, city_id, city_name, product_id, product_name)


def _handle_done(
    wa_id:      str,
    selected_id: str | None,
    session:    dict,
) -> None:
    """
    After showing the price card the user sees two buttons:
      btn_otro   → same city, new product
      btn_inicio → reset to start
    Anything else: remind them to use the buttons.
    """
    if selected_id == "btn_otro":
        city_id   = session["city_id"]
        city_name = session["city_name"]
        sm.transition_to_product(wa_id, city_id=city_id, city_name=city_name)
        _send_product_list(wa_id, city_name)

    else:
        # Unexpected input after price card
        sender.send_text(
            wa_id,
            "Usa los botones de abajo para consultar otro producto o volver al inicio. 👇"
        )


# ── Message builders ──────────────────────────────────────────────────────────

def _send_greeting_and_cities(wa_id: str) -> None:
    """Send the welcome text and then the city list menu."""
    sender.send_text(
        wa_id,
        "🌽 *Bienvenido a AgroPrecios*\n"
        "Consulta precios de mercado de la encuesta SIPSA del DANE.\n\n"
        "Primero, ¿en qué ciudad quieres consultar?"
    )

    cities = db.get_all_cities()
    items  = [
        {"id": f"city_{c['city_id']}", "title": c["city_name"]}
        for c in cities
    ]

    sender.send_list_message(
        wa_id   = wa_id,
        header  = "Ciudades disponibles",
        body    = "Selecciona tu ciudad:",
        items   = items,
        button_label = "Ver ciudades",
    )

    sm.transition_to_city(wa_id)


def _send_product_list(wa_id: str, city_name: str) -> None:
    """Send the product list for a given city."""
    products = db.get_all_products()
    items    = [
        {"id": f"prod_{p['product_id']}", "title": p["product_name"]}
        for p in products
    ]

    sender.send_list_message(
        wa_id   = wa_id,
        header  = f"Productos — {city_name}",
        body    = f"¿Qué producto quieres consultar en {city_name}?",
        items   = items,
        button_label = "Ver productos",
    )


def _send_price_card(
    wa_id:        str,
    city_id:      int,
    city_name:    str,
    product_id:   int,
    product_name: str,
) -> None:
    """Look up the latest price and send the result card + action buttons."""
    row = db.get_latest_price(city_id, product_id)

    if row is None:
        sender.send_text(
            wa_id,
            f"😔 No encontré precios recientes de *{product_name}* en *{city_name}*.\n"
            "Es posible que DANE no haya reportado datos para esta combinación."
        )
    else:
        price_fmt = f"${row['price_kilo']:,.0f}"
        date_fmt  = row["price_date"][:10] if row["price_date"] else "—"

        lines = [
            f"📦 *{product_name}*",
            f"📍 {city_name}",
            f"💰 Precio por kilo: *{price_fmt}*",
            f"📅 Fecha: {date_fmt}",
        ]

        # Unit-conversion disclaimer
        if row.get("is_converted_to_kg"):
            lines.append(
                "\n⚠️ _Este producto se vende normalmente por unidad o bulto. "
                "El precio fue convertido a kilogramo como referencia._"
            )

        sender.send_text(wa_id, "\n".join(lines))

    # Always show the follow-up buttons, even if no price was found
    sender.send_button_message(
        wa_id   = wa_id,
        text    = "¿Qué quieres hacer ahora?",
        buttons = [
            {"id": "btn_otro",   "title": "Otro producto"},
            {"id": "btn_inicio", "title": "Inicio"},
        ],
    )


# ── Utility ───────────────────────────────────────────────────────────────────

def _parse_int_id(raw_id: str, prefix: str) -> int | None:
    """
    Extract the integer from an ID like "city_3" or "prod_1001".
    Returns None if the format doesn't match.
    """
    if raw_id and raw_id.startswith(prefix):
        try:
            return int(raw_id[len(prefix):])
        except ValueError:
            pass
    logger.warning("Could not parse id '%s' with prefix '%s'", raw_id, prefix)
    return None


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok"}
