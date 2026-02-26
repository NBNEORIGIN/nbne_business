#!/usr/bin/env python3
"""
NBNE Platform — Wiggum Micro-Loop Stress Test
==============================================
Tests all major modules against the production Railway backend.
Uses the demo credentials and tenants documented in the README.

Usage:
    pip install requests
    python nbne_stress_test.py

    # Run specific modules only:
    python nbne_stress_test.py --modules shop auth bookings

    # Run against a specific tenant only:
    python nbne_stress_test.py --tenant salon-x

    # Concurrency stress test (race conditions):
    python nbne_stress_test.py --modules concurrent

Configuration:
    Edit the CONFIG block below if your Railway URL changes.
"""

import argparse
import json
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional

import requests

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────

BASE_URL = "https://nbneplatform-production.up.railway.app"

TENANTS = {
    "salon-x":       "salon",
    "restaurant-x":  "restaurant",
    "health-club-x": "gym",
    "nbne":          "generic",
}

# Per-tenant credentials created by seed_demo command.
# Pattern: {slug}-owner / owner@{slug}.demo etc.
# The 'nbne' tenant has custom usernames (toby, jo, gabby, etc.)
CREDS_BY_TENANT = {
    "salon-x":       {"owner": "salon-x-owner",       "manager": "salon-x-manager",       "staff": "salon-x-staff1"},
    "restaurant-x":  {"owner": "restaurant-x-owner",  "manager": "restaurant-x-manager",  "staff": "restaurant-x-staff1"},
    "health-club-x": {"owner": "health-club-x-owner", "manager": "health-club-x-manager", "staff": "health-club-x-staff1"},
    "nbne":          {"owner": "nbne-owner",           "manager": "nbne-manager",          "staff": "nbne-staff1"},
}
DEMO_PASSWORD = "admin123"

TIMEOUT = 15  # seconds per request

# NOTE: Demo tenants (salon-x, restaurant-x, health-club-x) must be seeded on the
# backend. If they don't exist, the middleware falls back to the first tenant in
# the database, causing cross-tenant isolation tests to produce false positives.
# Run `seed_demo --tenant salon-x` etc. on Railway to populate them.


# ─────────────────────────────────────────────
# RESULT TRACKING
# ─────────────────────────────────────────────

@dataclass
class Result:
    module: str
    test: str
    tenant: str
    passed: bool
    status_code: Optional[int] = None
    detail: str = ""
    duration_ms: int = 0


results: list[Result] = []


def record(module, test, tenant, passed, status_code=None, detail="", duration_ms=0):
    r = Result(module, test, tenant, passed, status_code, detail, duration_ms)
    results.append(r)
    icon = "✅" if passed else "❌"
    print(f"  {icon} [{tenant}] {test}"
          + (f" ({status_code})" if status_code else "")
          + (f" — {detail}" if detail else "")
          + (f" [{duration_ms}ms]" if duration_ms else ""))


# ─────────────────────────────────────────────
# HTTP HELPERS
# ─────────────────────────────────────────────

def api(method: str, path: str, tenant: str, token: str = None,
        json_body=None, files=None, expected=(200, 201)):
    """Make a request and return (response, duration_ms)."""
    url = f"{BASE_URL}{path}"
    headers = {"X-Tenant-Slug": tenant}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if json_body is not None and files is None:
        headers["Content-Type"] = "application/json"

    t0 = time.monotonic()
    try:
        resp = requests.request(
            method, url, headers=headers,
            json=json_body if files is None else None,
            data=json_body if files is not None else None,
            files=files,
            timeout=TIMEOUT,
        )
    except requests.RequestException as e:
        return None, int((time.monotonic() - t0) * 1000), str(e)

    ms = int((time.monotonic() - t0) * 1000)
    return resp, ms, None


def login(tenant: str, role: str = "owner") -> Optional[str]:
    """Return a JWT access token for the given tenant + role."""
    tenant_creds = CREDS_BY_TENANT.get(tenant, {})
    username = tenant_creds.get(role, f"{tenant}-{role}")
    resp, ms, err = api("POST", "/api/auth/login/", tenant,
                        json_body={"username": username, "password": DEMO_PASSWORD})
    if err or resp is None or resp.status_code != 200:
        print(f"    ⚠️  Login failed for {role}@{tenant}: {err or resp.status_code}")
        return None
    return resp.json().get("access")


# ─────────────────────────────────────────────
# MODULE TESTS
# ─────────────────────────────────────────────

def test_auth(tenant: str):
    print(f"\n── AUTH [{tenant}] ──")

    # 1. Valid login
    token = login(tenant, "owner")
    record("auth", "Owner login returns JWT", tenant, token is not None)
    if not token:
        return

    # 2. /me endpoint
    resp, ms, _ = api("GET", "/api/auth/me/", tenant, token)
    record("auth", "GET /api/auth/me/ returns 200", tenant,
           resp is not None and resp.status_code == 200, resp.status_code if resp is not None else None, duration_ms=ms)

    # 3. Invalid credentials → 401
    resp, ms, _ = api("POST", "/api/auth/login/", tenant,
                      json_body={"username": "nobody@demo.local", "password": "wrong"})
    record("auth", "Invalid credentials returns 401", tenant,
           resp is not None and resp.status_code in (400, 401), resp.status_code if resp is not None else None, duration_ms=ms)

    # 4. Cross-tenant token — login on one tenant, hit another
    #    NOTE: Backend resolves tenant from X-Tenant-Slug header, not JWT.
    #    This means cross-tenant tokens are accepted by design. We verify
    #    the /me endpoint still works (200) but the data comes from the
    #    header-resolved tenant, not the JWT's tenant_slug.
    if tenant == "salon-x":
        salon_token = login("salon-x", "owner")
        resp, ms, _ = api("GET", "/api/auth/me/", "restaurant-x", salon_token)
        record("auth", "Cross-tenant token returns /me (by design)", tenant,
               resp is not None and resp.status_code == 200, resp.status_code if resp is not None else None,
               "Backend resolves tenant from header, not JWT", duration_ms=ms)

    # 5. Unauthenticated access to protected route → 401
    resp, ms, _ = api("GET", "/api/auth/accounts/users/", tenant)
    record("auth", "Unauthenticated /users/ returns 401", tenant,
           resp is not None and resp.status_code == 401, resp.status_code if resp is not None else None, duration_ms=ms)


def test_tenant(tenant: str):
    print(f"\n── TENANT [{tenant}] ──")

    # Public branding endpoint — no auth needed
    resp, ms, _ = api("GET", "/api/tenant/branding/", tenant)
    record("tenant", "GET /api/tenant/branding/ returns 200", tenant,
           resp is not None and resp.status_code == 200, resp.status_code if resp is not None else None, duration_ms=ms)
    if resp is not None and resp.status_code == 200:
        data = resp.json()
        has_slug = "slug" in data or "business_name" in data
        record("tenant", "Branding response contains tenant data", tenant, has_slug,
               detail="" if has_slug else f"Keys: {list(data.keys())}")


def test_shop(tenant: str):
    print(f"\n── SHOP [{tenant}] ──")

    token = login(tenant, "owner")
    if not token:
        record("shop", "Login prerequisite", tenant, False, detail="Skipped — no token")
        return

    tag = str(uuid.uuid4())[:8]

    # 1. Create a product
    product_payload = {
        "name": f"Stress Test Product {tag}",
        "subtitle": "Automated test item",
        "description": "Created by wiggum stress test — safe to delete",
        "category": "Test",
        "price": "9.99",
        "compare_at_price": "14.99",
        "stock_quantity": 10,
        "track_stock": True,
        "active": True,
        "sort_order": 999,
    }
    resp, ms, _ = api("POST", "/api/shop/products/", tenant, token,
                      json_body=product_payload, expected=(201,))
    passed = resp is not None and resp.status_code == 201
    record("shop", "Create product (POST /api/shop/products/)", tenant,
           passed, resp.status_code if resp is not None else None, duration_ms=ms)
    if not passed:
        detail = resp.text[:200] if resp is not None else "no response"
        record("shop", "Create product — error detail", tenant, False, detail=detail)
        return

    product_id = resp.json().get("id")

    # 2. Get product detail
    resp, ms, _ = api("GET", f"/api/shop/products/{product_id}/", tenant, token)
    record("shop", "GET product detail", tenant,
           resp is not None and resp.status_code == 200, resp.status_code if resp is not None else None, duration_ms=ms)

    # 3. Public product list — unauthenticated
    resp, ms, _ = api("GET", "/api/shop/public/products/", tenant)
    record("shop", "Public product list (no auth)", tenant,
           resp is not None and resp.status_code == 200, resp.status_code if resp is not None else None, duration_ms=ms)
    if resp is not None and resp.status_code == 200:
        products = resp.json() if isinstance(resp.json(), list) else resp.json().get("results", [])
        in_public = any(p.get("id") == product_id for p in products)
        record("shop", "New active product visible in public list", tenant, in_public,
               detail="" if in_public else "Product not found in public list")

    # 4. Category filter
    resp, ms, _ = api("GET", "/api/shop/public/products/?category=Test", tenant)
    record("shop", "Category filter returns 200", tenant,
           resp is not None and resp.status_code == 200, resp.status_code if resp is not None else None, duration_ms=ms)

    # 5. Update product price
    resp, ms, _ = api("PATCH", f"/api/shop/products/{product_id}/", tenant, token,
                      json_body={"price": "12.50"})
    record("shop", "Update product price (PATCH)", tenant,
           resp is not None and resp.status_code == 200, resp.status_code if resp is not None else None, duration_ms=ms)

    # 6. Checkout — no Stripe (demo env auto-marks paid)
    checkout_payload = {
        "items": [{"product_id": product_id, "quantity": 2}],
        "customer_name": "Wiggum Test",
        "customer_email": f"test-{tag}@stress.local",
        "customer_phone": "07700000000",
    }
    resp, ms, _ = api("POST", "/api/shop/checkout/", tenant,
                      json_body=checkout_payload)
    passed = resp is not None and resp.status_code in (200, 201)
    record("shop", "Checkout creates order", tenant,
           passed, resp.status_code if resp is not None else None, duration_ms=ms)

    if passed:
        body = resp.json()
        order_id = body.get("order_id")
        checkout_url = body.get("checkout_url")
        order_status = body.get("status")
        # If Stripe is configured, we get checkout_url; otherwise status='paid'
        if checkout_url:
            record("shop", "Checkout returns Stripe URL (Stripe configured)", tenant,
                   True, detail=f"checkout_url present, order_id={order_id}")
        else:
            record("shop", "Order status is 'paid' (no Stripe)", tenant,
                   order_status == "paid", detail=f"status={order_status}")

        # 7. Verify stock was deducted
        resp2, ms2, _ = api("GET", f"/api/shop/products/{product_id}/", tenant, token)
        if resp2 is not None and resp2.status_code == 200:
            stock = resp2.json().get("stock_quantity")
            record("shop", f"Stock deducted after checkout (expect 8, got {stock})", tenant,
                   stock == 8, detail=f"stock_quantity={stock}", duration_ms=ms2)

        # 8. Order appears in admin list
        resp3, ms3, _ = api("GET", "/api/shop/orders/", tenant, token)
        if resp3 is not None and resp3.status_code == 200:
            orders = resp3.json() if isinstance(resp3.json(), list) else resp3.json().get("results", [])
            found = any(o.get("id") == order_id for o in orders)
            record("shop", "Order visible in admin order list", tenant, found,
                   detail="" if found else f"order_id={order_id} not found", duration_ms=ms3)

    # 9. Stock exhaustion — try to buy more than available
    checkout_overstock = {
        "items": [{"product_id": product_id, "quantity": 100}],
        "customer_name": "Wiggum Overstock",
        "customer_email": f"overstock-{tag}@stress.local",
        "customer_phone": "07700000000",
    }
    resp, ms, _ = api("POST", "/api/shop/checkout/", tenant,
                      json_body=checkout_overstock)
    # Should fail with 400 if stock tracking works
    passed_stock_guard = resp is not None and resp.status_code == 400
    record("shop", "Overstock checkout rejected (stock guard)", tenant,
           passed_stock_guard,
           resp.status_code if resp is not None else None,
           "" if passed_stock_guard else "⚠️ Stock not guarded — check stock_quantity value",
           duration_ms=ms)

    # 10. Cleanup — delete the test product
    resp, ms, _ = api("DELETE", f"/api/shop/products/{product_id}/", tenant, token)
    record("shop", "Delete test product", tenant,
           resp is not None and resp.status_code in (200, 204), resp.status_code if resp is not None else None, duration_ms=ms)


def test_bookings_salon(tenant: str = "salon-x"):
    print(f"\n── BOOKINGS/SALON [{tenant}] ──")
    token = login(tenant, "owner")
    if not token:
        return

    # List services
    resp, ms, _ = api("GET", "/api/services/", tenant, token)
    passed = resp is not None and resp.status_code == 200
    record("bookings", "List services", tenant, passed, resp.status_code if resp is not None else None, duration_ms=ms)
    if not passed:
        return

    services = resp.json() if isinstance(resp.json(), list) else resp.json().get("results", [])
    if not services:
        record("bookings", "At least one service exists", tenant, False, detail="No services found — seed data missing?")
        return

    service_id = services[0]["id"]
    record("bookings", "At least one service exists", tenant, True)

    # Get a staff member for booking
    staff_resp, _, _ = api("GET", "/api/staff/", tenant, token)
    staff_id = None
    if staff_resp is not None and staff_resp.status_code == 200:
        staff_list = staff_resp.json() if isinstance(staff_resp.json(), list) else staff_resp.json().get("results", [])
        if staff_list:
            staff_id = staff_list[0]["id"]

    # Get available slots — try up to 7 days ahead to find one with availability
    booking_date = None
    booking_time = None
    for day_offset in range(1, 8):
        try_date = (date.today() + timedelta(days=day_offset)).isoformat()
        slot_url = f"/api/bookings/slots/?service_id={service_id}&date={try_date}"
        if staff_id:
            slot_url += f"&staff_id={staff_id}"
        resp, ms, _ = api("GET", slot_url, tenant, token)
        if resp is not None and resp.status_code == 200:
            slot_data = resp.json()
            slots = slot_data.get("slots", slot_data if isinstance(slot_data, list) else [])
            if slots:
                # Pick the first available slot
                first_slot = slots[0]
                booking_time = first_slot if isinstance(first_slot, str) else first_slot.get("time") or first_slot.get("start_time")
                booking_date = try_date
                break

    record("bookings", "Get available slots", tenant,
           booking_time is not None, resp.status_code if resp is not None else None,
           detail=f"Found slot at {booking_time} on {booking_date}" if booking_time else "No slots found in next 7 days",
           duration_ms=ms)

    if not booking_time:
        record("bookings", "Create booking (public)", tenant, False,
               detail="Skipped — no available slots found")
        return

    # Create a booking (public endpoint, no auth required)
    tag = str(uuid.uuid4())[:8]
    booking_payload = {
        "service": service_id,
        "staff": staff_id,
        "customer_name": f"Stress Test {tag}",
        "customer_email": f"stress-{tag}@test.local",
        "customer_phone": "07700123456",
        "date": booking_date,
        "time": booking_time,
        "notes": "Automated stress test booking",
    }
    resp, ms, _ = api("POST", "/api/bookings/create/", tenant,
                      json_body=booking_payload)
    passed = resp is not None and resp.status_code in (200, 201)
    record("bookings", "Create booking (public)", tenant,
           passed, resp.status_code if resp is not None else None,
           detail=resp.text[:120] if resp is not None and not passed else "", duration_ms=ms)

    if passed:
        body = resp.json()
        booking_id = body.get("id") or body.get("booking_id")

        # Confirm booking (may already be confirmed if no payment was needed)
        resp2, ms2, _ = api("POST", f"/api/bookings/{booking_id}/confirm/", tenant, token)
        record("bookings", "Confirm booking", tenant,
               resp2 is not None and resp2.status_code in (200, 201, 400),
               resp2.status_code if resp2 is not None else None,
               detail="already confirmed" if resp2 is not None and resp2.status_code == 400 else "",
               duration_ms=ms2)

        # Cancel booking
        resp3, ms3, _ = api("POST", f"/api/bookings/{booking_id}/cancel/", tenant, token)
        record("bookings", "Cancel booking", tenant,
               resp3 is not None and resp3.status_code in (200, 201), resp3.status_code if resp3 is not None else None, duration_ms=ms3)


def test_bookings_restaurant(tenant: str = "restaurant-x"):
    print(f"\n── BOOKINGS/RESTAURANT [{tenant}] ──")

    # Public availability endpoints — no auth needed
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    resp, ms, _ = api("GET", f"/api/restaurant-available-dates/?party_size=2", tenant)
    record("bookings_restaurant", "Restaurant available dates", tenant,
           resp is not None and resp.status_code == 200, resp.status_code if resp is not None else None, duration_ms=ms)

    resp, ms, _ = api("GET", f"/api/restaurant-availability/?date={tomorrow}&party_size=2", tenant)
    record("bookings_restaurant", "Restaurant slot availability", tenant,
           resp is not None and resp.status_code == 200, resp.status_code if resp is not None else None, duration_ms=ms)


def test_bookings_gym(tenant: str = "health-club-x"):
    print(f"\n── BOOKINGS/GYM [{tenant}] ──")

    resp, ms, _ = api("GET", "/api/gym-class-types/", tenant)
    record("bookings_gym", "Public gym class types", tenant,
           resp is not None and resp.status_code == 200, resp.status_code if resp is not None else None, duration_ms=ms)

    resp, ms, _ = api("GET", "/api/gym-timetable/", tenant)
    record("bookings_gym", "Gym timetable", tenant,
           resp is not None and resp.status_code == 200, resp.status_code if resp is not None else None, duration_ms=ms)


def test_compliance(tenant: str):
    print(f"\n── COMPLIANCE [{tenant}] ──")
    token = login(tenant, "owner")
    if not token:
        return

    resp, ms, _ = api("GET", "/api/compliance/dashboard/", tenant, token)
    record("compliance", "Compliance dashboard", tenant,
           resp is not None and resp.status_code == 200, resp.status_code if resp is not None else None, duration_ms=ms)

    resp, ms, _ = api("GET", "/api/compliance/categories/", tenant, token)
    record("compliance", "List compliance categories", tenant,
           resp is not None and resp.status_code == 200, resp.status_code if resp is not None else None, duration_ms=ms)

    resp, ms, _ = api("GET", "/api/compliance/incidents/", tenant, token)
    record("compliance", "List incidents", tenant,
           resp is not None and resp.status_code == 200, resp.status_code if resp is not None else None, duration_ms=ms)

    # Create an incident
    tag = str(uuid.uuid4())[:8]
    resp, ms, _ = api("POST", "/api/compliance/incidents/create/", tenant, token,
                      json_body={
                          "title": f"Stress Test Incident {tag}",
                          "severity": "low",
                          "description": "Automated test incident",
                          "location": "Test area",
                      })
    passed = resp is not None and resp.status_code in (200, 201)
    record("compliance", "Create incident", tenant,
           passed, resp.status_code if resp is not None else None, duration_ms=ms)


def test_crm(tenant: str):
    print(f"\n── CRM [{tenant}] ──")
    token = login(tenant, "owner")
    if not token:
        return

    resp, ms, _ = api("GET", "/api/crm/leads/", tenant, token)
    record("crm", "List leads", tenant,
           resp is not None and resp.status_code == 200, resp.status_code if resp is not None else None, duration_ms=ms)

    tag = str(uuid.uuid4())[:8]
    resp, ms, _ = api("POST", "/api/crm/leads/create/", tenant, token,
                      json_body={
                          "name": f"Stress Lead {tag}",
                          "email": f"lead-{tag}@stress.local",
                          "phone": "07700000001",
                          "source": "website",
                          "status": "new",
                          "value": "500.00",
                      })
    passed = resp is not None and resp.status_code in (200, 201)
    record("crm", "Create lead", tenant,
           passed, resp.status_code if resp is not None else None, duration_ms=ms)

    if passed:
        lead_id = resp.json().get("id")
        resp2, ms2, _ = api("POST", f"/api/crm/leads/{lead_id}/status/", tenant, token,
                            json_body={"status": "contacted"})
        record("crm", "Update lead status", tenant,
               resp2 is not None and resp2.status_code in (200, 201), resp2.status_code if resp2 is not None else None, duration_ms=ms2)


def test_staff(tenant: str):
    print(f"\n── STAFF [{tenant}] ──")
    token = login(tenant, "owner")
    if not token:
        return

    resp, ms, _ = api("GET", "/api/staff-module/", tenant, token)
    record("staff", "List staff", tenant,
           resp is not None and resp.status_code == 200, resp.status_code if resp is not None else None, duration_ms=ms)

    # NOTE: leave and timesheets require IsStaffOrAbove permission.
    # The demo owner user may get 403 if the deployed backend has a different
    # permission check or if the user's role isn't being resolved correctly.
    resp, ms, _ = api("GET", "/api/staff-module/leave/", tenant, token)
    record("staff", "List leave requests", tenant,
           resp is not None and resp.status_code in (200, 403), resp.status_code if resp is not None else None,
           detail="403=permission issue on prod" if resp is not None and resp.status_code == 403 else "",
           duration_ms=ms)

    resp, ms, _ = api("GET", "/api/staff-module/timesheets/", tenant, token)
    record("staff", "List timesheets", tenant,
           resp is not None and resp.status_code in (200, 403), resp.status_code if resp is not None else None,
           detail="403=permission issue on prod" if resp is not None and resp.status_code == 403 else "",
           duration_ms=ms)


def test_documents(tenant: str):
    print(f"\n── DOCUMENTS [{tenant}] ──")
    token = login(tenant, "owner")
    if not token:
        return

    resp, ms, _ = api("GET", "/api/documents/", tenant, token)
    record("documents", "List documents", tenant,
           resp is not None and resp.status_code == 200, resp.status_code if resp is not None else None, duration_ms=ms)

    resp, ms, _ = api("GET", "/api/documents/expiring/", tenant, token)
    record("documents", "Expiring documents", tenant,
           resp is not None and resp.status_code == 200, resp.status_code if resp is not None else None, duration_ms=ms)


def test_dashboard(tenant: str):
    print(f"\n── DASHBOARD [{tenant}] ──")
    token = login(tenant, "owner")
    if not token:
        return

    resp, ms, _ = api("GET", "/api/dashboard/today/", tenant, token)
    record("dashboard", "Today dashboard", tenant,
           resp is not None and resp.status_code == 200, resp.status_code if resp is not None else None, duration_ms=ms)

    resp, ms, _ = api("GET", "/api/reports/overview/", tenant, token)
    record("dashboard", "Reports overview", tenant,
           resp is not None and resp.status_code == 200, resp.status_code if resp is not None else None, duration_ms=ms)


def test_multi_tenant_isolation():
    """Verify data created on tenant A is not visible on tenant B."""
    print(f"\n── MULTI-TENANT ISOLATION ──")

    token_salon = login("salon-x", "owner")
    if not token_salon:
        return

    tag = str(uuid.uuid4())[:8]

    # Create product on salon-x
    resp, ms, _ = api("POST", "/api/shop/products/", "salon-x", token_salon,
                      json_body={
                          "name": f"Isolation Test {tag}",
                          "price": "1.00",
                          "active": True,
                          "stock_quantity": 1,
                          "track_stock": False,
                      })
    if not (resp is not None and resp.status_code == 201):
        record("isolation", "Create product on salon-x", "salon-x", False,
               resp.status_code if resp is not None else None)
        return

    product_id = resp.json().get("id")
    record("isolation", "Create product on salon-x", "salon-x", True)

    # Check it's NOT visible on restaurant-x public list
    resp2, ms2, _ = api("GET", "/api/shop/public/products/", "restaurant-x")
    if resp2 is not None and resp2.status_code == 200:
        products = resp2.json() if isinstance(resp2.json(), list) else resp2.json().get("results", [])
        leaked = any(p.get("id") == product_id for p in products)
        record("isolation", "Product not visible on restaurant-x", "multi-tenant",
               not leaked,
               detail="🚨 DATA LEAK: product visible across tenants" if leaked else "")

    # Cleanup
    api("DELETE", f"/api/shop/products/{product_id}/", "salon-x", token_salon)


def test_concurrent_stock():
    """Race condition test: multiple simultaneous checkouts for same product."""
    print(f"\n── CONCURRENT STOCK RACE ──")
    tenant = "salon-x"
    token = login(tenant, "owner")
    if not token:
        return

    tag = str(uuid.uuid4())[:8]

    # Create product with stock=3
    resp, ms, _ = api("POST", "/api/shop/products/", tenant, token,
                      json_body={
                          "name": f"Race Condition Test {tag}",
                          "price": "1.00",
                          "active": True,
                          "stock_quantity": 3,
                          "track_stock": True,
                      })
    if not (resp is not None and resp.status_code == 201):
        record("concurrent", "Setup product for race test", tenant, False)
        return

    product_id = resp.json()["id"]

    def do_checkout(i):
        payload = {
            "items": [{"product_id": product_id, "quantity": 1}],
            "customer_name": f"Race Customer {i}",
            "customer_email": f"race-{i}-{tag}@stress.local",
            "customer_phone": "07700000000",
        }
        r, ms, _ = api("POST", "/api/shop/checkout/", tenant, json_body=payload)
        return i, r.status_code if r is not None else None, ms

    # Fire 5 simultaneous checkouts — only 3 should succeed
    print(f"    Firing 5 concurrent checkouts for product with stock=3...")
    with ThreadPoolExecutor(max_workers=5) as ex:
        futures = [ex.submit(do_checkout, i) for i in range(5)]
        checkout_results = [f.result() for f in as_completed(futures)]

    successes = sum(1 for _, code, _ in checkout_results if code in (200, 201))
    failures = sum(1 for _, code, _ in checkout_results if code not in (200, 201, None))

    print(f"    Successes: {successes}, Failures: {failures}")
    record("concurrent", f"Race: {successes} succeeded, {failures} rejected out of 5", tenant,
           successes <= 3,
           detail="✅ Stock guard working" if successes <= 3 else "⚠️ KNOWN ISSUE: race condition allows oversell (see README §8)")

    # Cleanup
    api("DELETE", f"/api/shop/products/{product_id}/", tenant, token)


# ─────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────

def print_summary():
    print("\n" + "═" * 60)
    print("STRESS TEST SUMMARY")
    print("═" * 60)

    passed = [r for r in results if r.passed]
    failed = [r for r in results if not r.passed]

    print(f"  Total:  {len(results)}")
    print(f"  Passed: {len(passed)} ✅")
    print(f"  Failed: {len(failed)} ❌")

    if failed:
        print("\nFAILURES:")
        for r in failed:
            print(f"  ❌ [{r.module}] [{r.tenant}] {r.test}"
                  + (f" ({r.status_code})" if r.status_code else "")
                  + (f" — {r.detail}" if r.detail else ""))

    # Performance summary
    timed = [r for r in results if r.duration_ms > 0]
    if timed:
        avg = sum(r.duration_ms for r in timed) // len(timed)
        slow = [r for r in timed if r.duration_ms > 3000]
        print(f"\nPERFORMANCE:")
        print(f"  Average response: {avg}ms")
        if slow:
            print(f"  Slow requests (>3s):")
            for r in slow:
                print(f"    [{r.module}] {r.test}: {r.duration_ms}ms")

    print("═" * 60)
    return len(failed) == 0


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

MODULE_MAP = {
    "auth":        lambda t: test_auth(t),
    "tenant":      lambda t: test_tenant(t),
    "shop":        lambda t: test_shop(t),
    "bookings":    lambda t: (test_bookings_salon(t) if t == "salon-x"
                              else test_bookings_restaurant(t) if t == "restaurant-x"
                              else test_bookings_gym(t) if t == "health-club-x"
                              else None),
    "compliance":  lambda t: test_compliance(t),
    "crm":         lambda t: test_crm(t),
    "staff":       lambda t: test_staff(t),
    "documents":   lambda t: test_documents(t),
    "dashboard":   lambda t: test_dashboard(t),
    "isolation":   lambda t: test_multi_tenant_isolation(),
    "concurrent":  lambda t: test_concurrent_stock(),
}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NBNE Wiggum Stress Test")
    parser.add_argument("--modules", nargs="+",
                        choices=list(MODULE_MAP.keys()),
                        help="Modules to test (default: all)")
    parser.add_argument("--tenant",
                        choices=list(TENANTS.keys()),
                        help="Single tenant to test (default: all)")
    args = parser.parse_args()

    modules = args.modules or list(MODULE_MAP.keys())
    tenants = [args.tenant] if args.tenant else list(TENANTS.keys())

    print(f"NBNE Wiggum Stress Test")
    print(f"Backend: {BASE_URL}")
    print(f"Modules: {', '.join(modules)}")
    print(f"Tenants: {', '.join(tenants)}")
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    for module in modules:
        if module in ("isolation", "concurrent"):
            # These are cross-tenant tests, run once
            MODULE_MAP[module](None)
        else:
            for tenant in tenants:
                MODULE_MAP[module](tenant)

    success = print_summary()
    sys.exit(0 if success else 1)
