import logging
import os
import json
from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import PlainTextResponse
from dotenv import load_dotenv

load_dotenv()

# ─── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("agroprecios")

# ─── Config (from .env) ──────────────────────────────────────────────────────
VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "agroprecios_verify_token")

app = FastAPI(title="AgroPrecios WhatsApp Bot")


# ─── Health check ────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok"}


# ─── GET /webhook  — Meta verification handshake ────────────────────────────
@app.get("/webhook")
def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    """
    Meta calls this endpoint once when you register the webhook URL.
    It sends three query params; we must echo back hub.challenge if the
    verify token matches, otherwise return 403.
    """
    logger.info("Webhook verification request received.")
    logger.debug(
        "mode=%s  token=%s  challenge=%s", hub_mode, hub_verify_token, hub_challenge
    )

    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        logger.info("Webhook verified successfully.")
        return PlainTextResponse(content=hub_challenge, status_code=200)

    logger.warning(
        "Verification FAILED. Expected token '%s', got '%s'.",
        VERIFY_TOKEN,
        hub_verify_token,
    )
    raise HTTPException(status_code=403, detail="Verification failed")


# ─── POST /webhook  — Receive incoming messages ──────────────────────────────
@app.post("/webhook")
async def receive_message(request: Request):
    """
    Meta sends every incoming WhatsApp event here as a JSON payload.
    We log it fully so you can inspect the structure before building
    the conversation logic in Step 6.
    """
    body = await request.json()

    # Pretty-print the full payload to the log
    logger.info("Incoming webhook payload:\n%s", json.dumps(body, indent=2, ensure_ascii=False))

    # Walk through the nested structure to find the actual message
    try:
        for entry in body.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})

                # Statuses (delivered, read receipts) — log and skip
                for status in value.get("statuses", []):
                    logger.info(
                        "Status update — id=%s  status=%s",
                        status.get("id"),
                        status.get("status"),
                    )

                # Actual messages
                for msg in value.get("messages", []):
                    wa_id   = msg.get("from")          # sender's WhatsApp number
                    msg_id  = msg.get("id")
                    msg_type = msg.get("type")          # "text", "interactive", etc.

                    if msg_type == "text":
                        text = msg["text"]["body"]
                        logger.info(
                            "TEXT message — from=%s  id=%s  body=%r",
                            wa_id, msg_id, text,
                        )

                    elif msg_type == "interactive":
                        interactive = msg.get("interactive", {})
                        i_type = interactive.get("type")  # "list_reply" or "button_reply"

                        if i_type == "list_reply":
                            reply_id    = interactive["list_reply"]["id"]
                            reply_title = interactive["list_reply"]["title"]
                            logger.info(
                                "LIST REPLY — from=%s  id=%s  reply_id=%s  title=%r",
                                wa_id, msg_id, reply_id, reply_title,
                            )

                        elif i_type == "button_reply":
                            reply_id    = interactive["button_reply"]["id"]
                            reply_title = interactive["button_reply"]["title"]
                            logger.info(
                                "BUTTON REPLY — from=%s  id=%s  reply_id=%s  title=%r",
                                wa_id, msg_id, reply_id, reply_title,
                            )

                    else:
                        logger.info(
                            "OTHER message type=%r — from=%s  id=%s",
                            msg_type, wa_id, msg_id,
                        )

    except Exception as exc:
        # Never crash on a malformed payload — Meta retries on 5xx
        logger.exception("Error parsing payload: %s", exc)

    # Meta requires a 200 response, otherwise it will retry the delivery
    return {"status": "ok"}
