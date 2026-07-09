"""
sender.py — AgroPrecios WhatsApp Message Sender
------------------------------------------------
Three functions to send every message type the bot needs:

  send_text(wa_id, text)
  send_list_message(wa_id, header, body, items)   <- city / product menus
  send_button_message(wa_id, text, buttons)        <- "Otro producto / Inicio"

Configuration via environment variables:
  WHATSAPP_TOKEN      — Meta Cloud API access token
  WHATSAPP_PHONE_ID   — WhatsApp Business phone number ID

Meta list message hard limit: 10 rows TOTAL per message (not per section).
When items > 10, this module sends multiple messages automatically.
"""

import os
import math
import json
import logging
import requests

logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────

TOKEN    = os.getenv("WHATSAPP_TOKEN",    "EAANHhTtyHPwBR1qzFIRWyQ0fXfTS6Un06zRE5e0ptB6G30HpRdBPuLPH2MYEMZCT16SkGZA52cE1iUhIet7a6DOdBR3KsCbhkcy6l9AsiFmXv5ZCXQZAEmejtLITY5VpRMHxpiXWSD9Jh2SKJIWLx5ICmGObHkNL0eAWa0Rgv3EMKghG4oKMFdLZBVuI4vcDZA9wZDZD")
PHONE_ID = os.getenv("WHATSAPP_PHONE_ID", "1170631419461622")
API_URL  = f"https://graph.facebook.com/v19.0/{PHONE_ID}/messages"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type":  "application/json",
}

# Meta hard limits (confirmed from API error)
_MAX_ROWS_PER_MESSAGE = 10   # total rows across ALL sections in one list message
_MAX_BUTTONS          = 3    # quick-reply buttons per button message


# ── Internal helper ───────────────────────────────────────────────────────────

def _post(payload: dict) -> dict:
    resp = requests.post(API_URL, headers=HEADERS, json=payload, timeout=10)
    if not resp.ok:
        print(f"\n Meta API error {resp.status_code}:")
        try:
            print(json.dumps(resp.json(), indent=2))
        except Exception:
            print(resp.text)
        resp.raise_for_status()
    return resp.json()


# ── Public API ────────────────────────────────────────────────────────────────

def send_text(wa_id: str, text: str) -> dict:
    payload = {
        "messaging_product": "whatsapp",
        "to": wa_id,
        "type": "text",
        "text": {"preview_url": False, "body": text},
    }
    result = _post(payload)
    logger.info("send_text → %s | message_id=%s", wa_id, result.get("messages", [{}])[0].get("id"))
    return result


def send_list_message(
    wa_id:        str,
    header:       str,
    body:         str,
    items:        list,   # each dict: {"id": str, "title": str}
    button_label: str = "Ver opciones",
) -> list:
    """
    Send an interactive list message.

    Meta allows max 10 rows TOTAL per message. If items > 10, this function
    sends multiple messages (e.g. 13 cities → message 1 with 10, message 2
    with 3) and returns a list of all API responses.

    Args:
        wa_id:         Recipient phone number (country code, no +).
        header:        Shown in the first message only (max 60 chars, no emojis).
        body:          Main prompt text (max 1024 chars).
        items:         List of {"id": str, "title": str} dicts.
        button_label:  Button that opens the list (max 20 chars, no emojis).
    """
    if not items:
        raise ValueError("send_list_message: items list is empty")

    total_messages = math.ceil(len(items) / _MAX_ROWS_PER_MESSAGE)
    responses = []

    for msg_index, batch_start in enumerate(range(0, len(items), _MAX_ROWS_PER_MESSAGE)):
        batch = items[batch_start : batch_start + _MAX_ROWS_PER_MESSAGE]

        rows = [
            {"id": str(item["id"]), "title": str(item["title"])[:24]}
            for item in batch
        ]

        # All rows go in a single section (the 10-row limit is per message, not per section)
        if total_messages > 1:
            section_title = f"Parte {msg_index + 1} de {total_messages}"
        else:
            section_title = "Opciones"

        # Only show the instructional body on the first message
        if msg_index == 0:
            msg_body = body[:1024]
        else:
            msg_body = f"Continuacion ({msg_index + 1}/{total_messages}):"

        payload = {
            "messaging_product": "whatsapp",
            "to": wa_id,
            "type": "interactive",
            "interactive": {
                "type": "list",
                "body": {"text": msg_body},
                "action": {
                    "button": button_label[:20],
                    "sections": [
                        {"title": section_title, "rows": rows}
                    ],
                },
            },
        }

        result = _post(payload)
        logger.info(
            "send_list_message → %s | batch %d/%d (%d rows) | message_id=%s",
            wa_id, msg_index + 1, total_messages, len(batch),
            result.get("messages", [{}])[0].get("id"),
        )
        responses.append(result)

    return responses


def send_button_message(
    wa_id:   str,
    text:    str,
    buttons: list,   # each dict: {"id": str, "title": str}
) -> dict:
    """
    Send an interactive quick-reply button message (max 3 buttons).
    """
    if not buttons:
        raise ValueError("send_button_message: buttons list is empty")

    if len(buttons) > _MAX_BUTTONS:
        logger.warning("send_button_message: trimming to %d buttons", _MAX_BUTTONS)
        buttons = buttons[:_MAX_BUTTONS]

    meta_buttons = [
        {"type": "reply", "reply": {"id": str(b["id"]), "title": str(b["title"])[:20]}}
        for b in buttons
    ]

    payload = {
        "messaging_product": "whatsapp",
        "to": wa_id,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body":   {"text": text[:1024]},
            "action": {"buttons": meta_buttons},
        },
    }

    result = _post(payload)
    logger.info(
        "send_button_message → %s | buttons=%d | message_id=%s",
        wa_id, len(buttons), result.get("messages", [{}])[0].get("id"),
    )
    return result
