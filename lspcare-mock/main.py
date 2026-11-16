"""
LSPcare API mock — just enough to let the Bland pathway run end-to-end.

Not production code. Returns fixture responses keyed by device_id prefix so test
scenarios can hit different branches of the pathway deterministically.

Device ID prefixes that trigger specific scenarios:
    test-ok       happy path (default)
    test-404      device not found
    test-active   device has an active package already
    test-loading  payment currently loading (<5 min)
    test-adv-used earlier pay-later already used this stay
    test-owing    earlier pay-later unpaid

Run:
    pip install -r requirements.txt
    MOCK_BEARER=changeme uvicorn main:app --host 0.0.0.0 --port 8099 --reload
"""

import os
import random
from datetime import datetime, timezone, timedelta
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel

BEARER = os.environ.get("MOCK_BEARER", "changeme")

app = FastAPI(title="LSPcare mock API", version="0.1.0")


def _auth(authorization: str | None) -> None:
    expected = f"Bearer {BEARER}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="bad bearer token")


def _brisbane_now() -> datetime:
    # AEST, UTC+10, no daylight saving
    return datetime.now(timezone.utc) + timedelta(hours=10)


def _helpdesk_open() -> bool:
    now = _brisbane_now()
    # Mon-Fri 08:30-17:00 Brisbane
    if now.weekday() >= 5:
        return False
    minutes = now.hour * 60 + now.minute
    return 8 * 60 + 30 <= minutes < 17 * 60


def _scenario(device_id: str) -> str:
    if not device_id:
        return "ok"
    for prefix in ("test-404", "test-active", "test-loading",
                   "test-adv-used", "test-owing", "test-ok"):
        if device_id.startswith(prefix):
            return prefix.removeprefix("test-")
    return "ok"


# -- 1. Find device -----------------------------------------------------------

class FindDeviceReq(BaseModel):
    hospital: str | None = None
    device_id: str | None = None
    bed_id: str | None = None
    call_id: str | None = None


@app.post("/hospitals/{hospital}/devices/lookup")
def find_device(hospital: str, body: FindDeviceReq,
                authorization: str | None = Header(default=None)) -> dict[str, Any]:
    _auth(authorization)
    scenario = _scenario(body.device_id or "")

    if scenario == "404":
        return {
            "device_found": False, "device_id": None, "package_active": False,
            "ends_at": None, "payment_pending_minutes": None,
            "advance_used": False, "balance_owing": False,
            "helpdesk_open": _helpdesk_open(),
        }

    base = {
        "device_found": True,
        "device_id": body.device_id or "86e7e12",
        "package_active": False,
        "ends_at": None,
        "payment_pending_minutes": None,
        "advance_used": False,
        "balance_owing": False,
        "helpdesk_open": _helpdesk_open(),
    }
    if scenario == "active":
        base["package_active"] = True
        base["ends_at"] = (_brisbane_now() + timedelta(hours=18)).strftime("%a %-d %b, %-I:%M %p")
    elif scenario == "loading":
        base["payment_pending_minutes"] = 2
    elif scenario == "adv-used":
        base["advance_used"] = True
    elif scenario == "owing":
        base["balance_owing"] = True
    return base


# -- 2. Pay-later check -------------------------------------------------------

class AdvanceReq(BaseModel):
    hospital: str | None = None
    device_id: str | None = None
    bed_id: str | None = None
    contact_name: str | None = None
    mobile: str | None = None
    email: str | None = None
    pay_by: str | None = None
    call_id: str | None = None


@app.post("/devices/{device_id}/advance")
def advance(device_id: str, body: AdvanceReq,
            authorization: str | None = Header(default=None)) -> dict[str, Any]:
    _auth(authorization)
    scenario = _scenario(device_id)

    if scenario == "404":
        return {"approved": False, "reason": "device_not_found", "ends_at": None}
    if scenario == "active":
        return {"approved": False, "reason": "package_active", "ends_at": None}
    if scenario == "loading":
        return {"approved": False, "reason": "payment_loading", "ends_at": None}
    if scenario == "adv-used":
        return {"approved": False, "reason": "advance_used", "ends_at": None}
    if scenario == "owing":
        return {"approved": False, "reason": "unpaid_advance", "ends_at": None}

    ends_at = (_brisbane_now() + timedelta(hours=24)).strftime("%a %-d %b, %-I:%M %p")
    return {"approved": True, "reason": None, "ends_at": ends_at}


# -- 3. Payment link by SMS ---------------------------------------------------

class PaymentLinkReq(BaseModel):
    mobile: str
    hospital: str | None = None
    device_id: str | None = None
    pay_by: str | None = None
    advance_granted: str | bool | None = None
    call_id: str | None = None


@app.post("/payment-links")
def payment_link(body: PaymentLinkReq,
                 authorization: str | None = Header(default=None)) -> dict[str, Any]:
    _auth(authorization)
    last4 = "".join(c for c in (body.mobile or "") if c.isdigit())[-4:] or "0000"
    return {"sms_sent": True, "mobile_last4": last4}


# -- 4. Log ticket ------------------------------------------------------------

class TicketReq(BaseModel):
    hospital: str | None = None
    device_id: str | None = None
    bed_id: str | None = None
    contact_name: str | None = None
    mobile: str | None = None
    callback_time: str | None = None
    reason: str | None = None
    intent: str | None = None
    call_id: str | None = None
    port_label: str | None = None
    screen_state: str | None = None
    screen_description: str | None = None


@app.post("/tickets")
def ticket(body: TicketReq,
           authorization: str | None = Header(default=None)) -> dict[str, Any]:
    _auth(authorization)
    return {"ticket_id": f"LSP-{random.randint(10000, 99999)}"}


# -- 5. Send invoice by SMS ---------------------------------------------------

class InvoiceReq(BaseModel):
    hospital: str | None = None
    device_id: str | None = None
    invoice_period: str | None = None
    invoice_package: str | None = None
    mobile: str
    call_id: str | None = None


@app.post("/invoices/send-sms")
def invoice(body: InvoiceReq,
            authorization: str | None = Header(default=None)) -> dict[str, Any]:
    _auth(authorization)
    last4 = "".join(c for c in (body.mobile or "") if c.isdigit())[-4:] or "0000"
    # Pretend invoice_count = 0 for a specific test device so node 12d can be exercised
    if body.device_id and body.device_id.startswith("test-no-invoice"):
        return {"invoice_sent": False, "invoice_count": 0, "mobile_last4": last4}
    return {"invoice_sent": True, "invoice_count": 1, "mobile_last4": last4}


@app.get("/")
def root() -> dict[str, str]:
    return {"status": "ok", "service": "lspcare-mock",
            "helpdesk_open": str(_helpdesk_open())}
