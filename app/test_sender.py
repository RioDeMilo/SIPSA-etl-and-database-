"""
test_sender.py — Live end-to-end test for sender.py
----------------------------------------------------
Run with:
    python test_sender.py <your_whatsapp_number>

<your_whatsapp_number> must include the country code, no '+':
    python test_sender.py 573001234567
"""

import sys
import json
import logging
from sender import send_text, send_list_message, send_button_message

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    wa_id = sys.argv[1].strip().lstrip("+")
    print(f"\n=== AgroPrecios sender test → {wa_id} ===\n")

    # ── Test 1: plain text ────────────────────────────────────────────────────
    print("1) Sending plain text message...")
    r1 = send_text(
        wa_id,
        "AgroPrecios - prueba de mensajeria\n\n"
        "Hola! Este es un mensaje de texto de prueba. "
        "Los siguientes mensajes muestran la lista de ciudades y los botones de accion."
    )
    print("   Response:", json.dumps(r1, indent=2))

    # ── Test 2: list message with 13 items (triggers 2 sections) ─────────────
    print("\n2) Sending list message (13 cities, 2 sections)...")

    sample_cities = [
        {"id": "1",  "title": "Bogota"},
        {"id": "2",  "title": "Medellin"},
        {"id": "3",  "title": "Cali"},
        {"id": "4",  "title": "Barranquilla"},
        {"id": "5",  "title": "Bucaramanga"},
        {"id": "6",  "title": "Manizales"},
        {"id": "7",  "title": "Pereira"},
        {"id": "8",  "title": "Cucuta"},
        {"id": "9",  "title": "Ibague"},
        {"id": "10", "title": "Cartagena"},
        {"id": "11", "title": "Villavicencio"},
        {"id": "12", "title": "Pasto"},
        {"id": "13", "title": "Armenia"},
    ]

    r2 = send_list_message(
        wa_id,
        header="Selecciona tu ciudad",
        body="En que ciudad quieres consultar los precios?\nElige una opcion de la lista:",
        items=sample_cities,
        button_label="Ver ciudades",
    )
    print("   Responses:", json.dumps(r2, indent=2))

    # ── Test 3: button message ────────────────────────────────────────────────
    print("\n3) Sending button message...")
    r3 = send_button_message(
        wa_id,
        text=(
            "Precio registrado\n\n"
            "Ciudad: Bogota\n"
            "Producto: Brocoli\n"
            "Precio: $2.450 / kg\n"
            "Fecha: 2025-06-18\n\n"
            "Que deseas hacer ahora?"
        ),
        buttons=[
            {"id": "otro_producto", "title": "Otro producto"},
            {"id": "inicio",        "title": "Inicio"},
        ],
    )
    print("   Response:", json.dumps(r3, indent=2))

    print("\n=== All messages sent! Check your WhatsApp. ===\n")


if __name__ == "__main__":
    main()
