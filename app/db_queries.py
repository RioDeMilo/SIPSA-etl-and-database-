"""
db_queries.py — AgroPrecios SQLite query module
------------------------------------------------
Provides three public functions consumed by the WhatsApp bot:
  - get_all_cities()      → city list for the menu
  - get_all_products()    → product list for the menu
  - get_latest_price()    → most recent price for a city/product pair

Also exposes `run_migrations()` which should be called once on startup
to ensure the `is_converted_to_kg` column exists in the `productos` table.
"""

import sqlite3
from pathlib import Path
from typing import Optional

# ── Path configuration ────────────────────────────────────────────────────────
# Adjust this to wherever agro.db lives on your server.
# The default assumes this file sits at /agroprecios/app/db_queries.py
# and the database is at /agroprecios/database/agro.db
DB_PATH = Path(__file__).resolve().parent.parent / "database" / "agro.db"


def _get_conn(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """Open a connection with row_factory so rows come back as dicts."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row   # rows behave like dicts: row["campo"]
    return conn


# ── Migration ─────────────────────────────────────────────────────────────────

def run_migrations(db_path: Path = DB_PATH) -> None:
    """
    Idempotent: adds `is_converted_to_kg` to the productos table if absent.
    Safe to call every time the app starts.
    """
    conn = _get_conn(db_path)
    try:
        # Check existing columns
        columns = {
            row[1]
            for row in conn.execute("PRAGMA table_info(productos)")
        }
        if "is_converted_to_kg" not in columns:
            conn.execute(
                "ALTER TABLE productos ADD COLUMN is_converted_to_kg INTEGER NOT NULL DEFAULT 0"
            )
            conn.commit()
            print("[migration] Added `is_converted_to_kg` column to `productos`.")
        else:
            print("[migration] `is_converted_to_kg` already present — skipping.")
    finally:
        conn.close()


# ── Query functions ───────────────────────────────────────────────────────────

def get_all_cities(db_path: Path = DB_PATH) -> list[dict]:
    """
    Returns every city ordered alphabetically.

    Return format:
        [{"city_id": 1, "city_name": "Bogotá"}, ...]
    """
    conn = _get_conn(db_path)
    try:
        rows = conn.execute(
            "SELECT ciudad_id AS city_id, ciudad_nombre AS city_name "
            "FROM ciudades ORDER BY ciudad_nombre"
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_all_products(db_path: Path = DB_PATH) -> list[dict]:
    """
    Returns every product ordered by name.

    Return format:
        [{"product_id": 1001, "product_name": "Papa pastusa", "is_converted_to_kg": 0}, ...]
    """
    conn = _get_conn(db_path)
    try:
        rows = conn.execute(
            "SELECT producto_id    AS product_id, "
            "       producto_nombre AS product_name, "
            "       is_converted_to_kg "
            "FROM productos ORDER BY producto_nombre"
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_latest_price(
    city_id: int,
    product_id: int,
    db_path: Path = DB_PATH,
) -> Optional[dict]:
    """
    Returns the most recent price row for a given city and product.

    Uses `precio_fecha DESC` to find the latest record; ties broken by
    `precio_id DESC` so the highest ID wins.

    Return format (or None if no data):
        {
          "price_id":    5,
          "product_id":  1001,
          "product_name":"Papa pastusa",
          "city_id":     1,
          "city_name":   "Bogotá",
          "price_kilo":  1900.0,
          "price_date":  "2025-06-16",
          "is_converted_to_kg": 0,
        }
    """
    conn = _get_conn(db_path)
    try:
        row = conn.execute(
            """
            SELECT
                p.precio_id            AS price_id,
                p.producto_id          AS product_id,
                pr.producto_nombre     AS product_name,
                p.ciudad_id            AS city_id,
                c.ciudad_nombre        AS city_name,
                p.precio_kilo          AS price_kilo,
                p.precio_fecha         AS price_date,
                pr.is_converted_to_kg  AS is_converted_to_kg
            FROM precios p
            JOIN productos pr ON pr.producto_id = p.producto_id
            JOIN ciudades  c  ON c.ciudad_id    = p.ciudad_id
            WHERE p.ciudad_id  = ?
              AND p.producto_id = ?
            ORDER BY p.precio_fecha DESC, p.precio_id DESC
            LIMIT 1
            """,
            (city_id, product_id),
        ).fetchone()

        return dict(row) if row else None
    finally:
        conn.close()
