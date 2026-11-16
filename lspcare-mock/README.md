# LSPcare mock API

Mock implementation of the 5 LSPcare backend endpoints the Bland pathway calls. Stands in for the real LSPcare API so the Bland POC can run end-to-end without touching production.

**For the full setup walkthrough see [`BLAND-SETUP.md`](BLAND-SETUP.md).**

## Files

| File | What it is |
|---|---|
| `main.py` | FastAPI app, 5 endpoints, bearer auth, scenario-keyed fixtures |
| `requirements.txt` | Python deps (fastapi, uvicorn, pydantic) |
| `run.sh` | One command: install deps, run uvicorn, open Cloudflare quick tunnel |
| `BLAND-SETUP.md` | End-to-end guide: run mock → import pathway → wire webhooks → test in Voice Chat |

## Quick start

```bash
cd ~/AGENT/lspcare-mock
./run.sh
```

Copy the bearer token and trycloudflare URL that print, then follow `BLAND-SETUP.md`.

## Endpoints

All require `Authorization: Bearer <token>`. 401 if missing or wrong.

| Method | Path | Called by pathway node | Purpose |
|---|---|---|---|
| POST | `/hospitals/{h}/devices/lookup` | 3 Find device | Device lookup |
| POST | `/devices/{id}/advance` | 7b No card | Pay-later eligibility |
| POST | `/payment-links` | 8 Send link by SMS | Issue tv.lsp.io link |
| POST | `/tickets` | 6, 9, 10b | Log callback / fault / escalation ticket |
| POST | `/invoices/send-sms` | 12b Send invoice | Email a receipt |
| GET | `/` | — | Health check |

## Test scenarios (device_id prefix)

| Prefix | Scenario |
|---|---|
| any | happy path |
| `test-404` | device not found |
| `test-active` | active package already |
| `test-loading` | payment loading (<5 min) |
| `test-adv-used` | earlier advance used this stay |
| `test-owing` | unpaid earlier advance |
| `test-no-invoice` | invoice endpoint returns zero matches |

## Not production

- No persistence, no database
- Timestamps are current + fixed offsets
- Ticket IDs are random
- No webhook signature validation
- Hospital names are not validated

The real LSPcare API exists separately — this mock only exists to let the Bland pathway run during POC testing without hitting production.
