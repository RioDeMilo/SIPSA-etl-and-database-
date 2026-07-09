"""
test_session_manager.py — AgroPrecios Bot
Simulates a full WhatsApp conversation without touching Meta's API.
Run with:  python test_session_manager.py

Covers:
  1. Fresh session is created at 'start'
  2. Normal flow: start → city → product → done
  3. "Otro producto" loop (stays on same city, picks new product)
  4. "Inicio" reset (wipes everything back to start)
  5. Unknown step raises ValueError
  6. Two users are isolated from each other
"""

import sys
import traceback
from session_manager import (
    get_session,
    set_step,
    reset_session,
    transition_to_city,
    transition_to_product,
    transition_to_done,
    next_step,
)

# ---------------------------------------------------------------------------
# Tiny test harness
# ---------------------------------------------------------------------------
PASS = "✅"
FAIL = "❌"
_results: list[tuple[str, bool]] = []


def check(label: str, condition: bool) -> None:
    icon = PASS if condition else FAIL
    print(f"  {icon}  {label}")
    _results.append((label, condition))


def section(title: str) -> None:
    print(f"\n{'─'*55}")
    print(f"  {title}")
    print(f"{'─'*55}")


# ---------------------------------------------------------------------------
# Fake user IDs
# ---------------------------------------------------------------------------
USER_A = "573001234567"   # farmer Alice
USER_B = "573009876543"   # farmer Bob

# Fake city / product data (as if returned by Step 3 query functions)
BOGOTA   = {"city_id": 1,  "city_name": "Bogotá"}
MEDELLIN = {"city_id": 2,  "city_name": "Medellín"}
PAPA     = {"product_id": 101, "product_name": "Papa pastusa"}
PLATANO  = {"product_id": 205, "product_name": "Plátano hartón"}

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

section("1 — Fresh session defaults")
session_a = get_session(USER_A)
print(f"     Session: {session_a}")
check("step is 'start'",         session_a["step"] == "start")
check("city_id is None",         session_a["city_id"] is None)
check("city_name is None",       session_a["city_name"] is None)
check("product_id is None",      session_a["product_id"] is None)
check("product_name is None",    session_a["product_name"] is None)
check("next_step → awaiting_city", next_step(session_a) == "awaiting_city")


section("2 — Bot sends city list → transition_to_city")
transition_to_city(USER_A)
session_a = get_session(USER_A)
print(f"     Session: {session_a}")
check("step is 'awaiting_city'",   session_a["step"] == "awaiting_city")
check("next_step → awaiting_product", next_step(session_a) == "awaiting_product")


section("3 — User picks Bogotá → transition_to_product")
transition_to_product(USER_A, **BOGOTA)
session_a = get_session(USER_A)
print(f"     Session: {session_a}")
check("step is 'awaiting_product'", session_a["step"] == "awaiting_product")
check("city_id == 1",               session_a["city_id"] == 1)
check("city_name == 'Bogotá'",      session_a["city_name"] == "Bogotá")
check("product_id still None",      session_a["product_id"] is None)
check("next_step → done",           next_step(session_a) == "done")


section("4 — User picks Papa → transition_to_done")
transition_to_done(USER_A, **PAPA)
session_a = get_session(USER_A)
print(f"     Session: {session_a}")
check("step is 'done'",             session_a["step"] == "done")
check("product_id == 101",          session_a["product_id"] == 101)
check("product_name == 'Papa pastusa'", session_a["product_name"] == "Papa pastusa")
check("city still Bogotá",          session_a["city_name"] == "Bogotá")
check("next_step → awaiting_product (loop)", next_step(session_a) == "awaiting_product")


section("5 — User taps 'Otro producto' (same city, new product)")
# Bot sends product list again; user picks Plátano
transition_to_product(USER_A, **BOGOTA)   # city stays the same
transition_to_done(USER_A, **PLATANO)
session_a = get_session(USER_A)
print(f"     Session: {session_a}")
check("step is 'done'",                    session_a["step"] == "done")
check("city still Bogotá",                 session_a["city_name"] == "Bogotá")
check("product_id == 205 (Plátano)",       session_a["product_id"] == 205)
check("product_name == 'Plátano hartón'",  session_a["product_name"] == "Plátano hartón")


section("6 — User taps 'Inicio' → reset_session")
reset_session(USER_A)
session_a = get_session(USER_A)
print(f"     Session: {session_a}")
check("step back to 'start'",   session_a["step"] == "start")
check("city_id wiped",          session_a["city_id"] is None)
check("city_name wiped",        session_a["city_name"] is None)
check("product_id wiped",       session_a["product_id"] is None)
check("product_name wiped",     session_a["product_name"] is None)


section("7 — Unknown step raises ValueError")
caught = False
try:
    set_step(USER_A, "made_up_step")
except ValueError as e:
    caught = True
    print(f"     Caught: {e}")
check("ValueError raised for bad step", caught)


section("8 — Two users are isolated (USER_B unaffected by USER_A's flow)")
# Simulate USER_B having their own separate conversation
transition_to_city(USER_B)
transition_to_product(USER_B, **MEDELLIN)
session_b = get_session(USER_B)
session_a = get_session(USER_A)   # USER_A was just reset
print(f"     USER_A session: {session_a}")
print(f"     USER_B session: {session_b}")
check("USER_B step is 'awaiting_product'", session_b["step"] == "awaiting_product")
check("USER_B city is Medellín",           session_b["city_name"] == "Medellín")
check("USER_A step is still 'start'",      session_a["step"] == "start")
check("USER_A city still None",            session_a["city_id"] is None)


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
total  = len(_results)
passed = sum(1 for _, ok in _results if ok)
failed = total - passed

print(f"\n{'═'*55}")
print(f"  Results: {passed}/{total} passed", end="")
if failed:
    print(f"  |  {failed} FAILED ← fix these before moving to Step 6")
    for label, ok in _results:
        if not ok:
            print(f"     {FAIL}  {label}")
else:
    print("  — all good, Step 4 complete! 🎉")
print(f"{'═'*55}\n")

sys.exit(0 if failed == 0 else 1)
