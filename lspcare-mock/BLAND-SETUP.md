# Bland POC — get the LSPcare pathway running end-to-end

The goal: import the pathway, wire the webhooks to the mock LSPcare API, and run through a few scenarios in Bland Voice Chat. No real phone number, no real LSPcare backend.

Three stages, ~30 minutes total. Do them in order.

---

## Stage 1 — Start the mock LSPcare API

The mock lives in this folder. It stands in for the real LSPcare backend so the webhook nodes in the pathway (Find device, Advance, Payment link, Tickets, Invoice) actually return realistic data.

### On the home server

```bash
cd ~/AGENT/lspcare-mock   # or /tmp/AGENT/lspcare-mock if you haven't moved it
./run.sh
```

What this does:

1. Generates a random bearer token and prints it (**copy this** — you paste it into Bland)
2. Installs the Python deps into a local venv
3. Boots uvicorn on `127.0.0.1:8099`
4. Opens a Cloudflare quick tunnel that exposes it at a public `https://<random>.trycloudflare.com` URL (**copy this URL too**)

You'll see something like:

```
Bearer token: 3f8a1b2c9e0d...
...
=== Cloudflare tunnel starting ===
...
Your quick Tunnel has been created! Visit it at:
https://smelly-badger-9823.trycloudflare.com
```

**Keep this terminal running** for the whole Bland session — closing it kills the tunnel.

### Verify it's reachable

In a second terminal:

```bash
curl https://<your-trycloudflare-url>/
# {"status":"ok","service":"lspcare-mock",...}
```

### Deterministic test scenarios

The mock keys responses off the `device_id` prefix so Voice Chat can hit specific branches:

| Say this Device ID | What the mock returns | Pathway branch tested |
|---|---|---|
| anything (e.g. `86e7e12`) | happy path, approve advance | Normal buy / No card happy path |
| `test-404` | device not found | Device-not-found → screen check |
| `test-active-01` | active package already | Already has package route |
| `test-loading-01` | payment loading, 2 min ago | "Paid but not working" <5 min route |
| `test-adv-used-01` | earlier advance used this stay | Pay-later declined (advance_used) |
| `test-owing-01` | unpaid earlier advance | Pay-later declined (unpaid_advance) |

---

## Stage 2 — Import the pathway into Bland and wire up

### 2a. Edit `lspcare-support-pathway.json` before importing

Two placeholders must be replaced. Do them with find-and-replace in your editor, or run the sed commands below.

**Replace API base URL** — appears in webhook nodes 3, 7b, 8, 10b, 12b:

```bash
sed -i 's|https://REPLACE-WITH-LSP-API-BASE|https://<your-trycloudflare-url>|g' \
  ~/AGENT/LSPcare-Support-Bland-Pack_3/lspcare-support-pathway.json
```

**Replace the transfer number** — appears in node 10c (warm transfer). For Voice Chat testing the transfer won't actually fire; a placeholder is fine. If you want it to try to transfer to your mobile for the live demo, use your real number:

```bash
sed -i 's|+61000000000|+61YOURMOBILE|g' \
  ~/AGENT/LSPcare-Support-Bland-Pack_3/lspcare-support-pathway.json
```

### 2b. Import into Bland

Two options — pick whichever works:

**Option A — Bland UI import**

1. Log in to `app.bland.ai`
2. Pathways → New Pathway → name it "LSPcare Support POC"
3. Open the pathway, find the Import / Update Pathway option
4. Paste the contents of `lspcare-support-pathway.json`

**Option B — API import (cleaner, repeatable)**

```bash
# Create an empty pathway first via the UI to get a pathway_id, then:
PATHWAY_ID=<the-id-from-step-above>
BLAND_API_KEY=<your-bland-api-key>

curl -X POST "https://api.bland.ai/v1/pathway/$PATHWAY_ID" \
  -H "authorization: $BLAND_API_KEY" \
  -H "Content-Type: application/json" \
  --data-binary @~/AGENT/LSPcare-Support-Bland-Pack_3/lspcare-support-pathway.json
```

### 2c. Set the bearer token as a Bland Secret

The mock expects `Authorization: Bearer <token>` on every webhook call.

1. In Bland, go to Secrets (or Vault, depending on UI version)
2. Add a new secret, name it `LSPCARE_MOCK_BEARER`, value = the token you copied from Stage 1
3. Open each webhook node in the pathway (3, 7b, 8, 10b, 12b)
4. In the node's headers, add:
   - **Key:** `Authorization`
   - **Value:** `Bearer {{secrets.LSPCARE_MOCK_BEARER}}` (exact syntax depends on Bland's current UI — the variable reference form may be `{{LSPCARE_MOCK_BEARER}}` or similar)

### 2d. Add fake hospital names

Open the Knowledge Base node (or upload text in Bland's Knowledge section). Edit `knowledge-base.txt` to replace the `[REPLACE WITH LSP'S HOSPITAL LIST]` placeholder with any 2–3 fake hospital names, e.g.:

```
HOSPITALS USING LSPCARE
- General Hospital (GH)
- Mercy Hospital (Mercy)
- St Andrews Private
```

This lets callers say "I'm at General Hospital" and get matched.

---

## Stage 3 — Test in Bland Voice Chat

1. Open the pathway in Bland
2. Click Voice Chat (or Test Call → Browser)
3. Allow microphone access

### Suggested test run order (hitting different branches)

Work through these in order. Each one takes 60-90 seconds.

**Test 1 — Happy "how do I buy" path**
- Greeting → "I'm at General Hospital" → "My bed is 6CW101" → "How do I buy?"
- Agent explains from KB, offers SMS link
- You accept → agent sends payment link
- Agent: "I've sent a link to the number ending in ..."
- **Expected mock hits:** `/devices/lookup` (happy), `/payment-links` (sent)

**Test 2 — Pay-later approved**
- "I'm at Mercy", "bed 4A01", "I don't have my card"
- Give a name, a mobile, say "I'll pay tomorrow at 10am"
- Agent reads the mobile back
- Agent: "I've turned on a 1 Day package..."
- **Expected mock hits:** `/devices/lookup` (happy), `/devices/{id}/advance` (approved), `/payment-links`

**Test 3 — Pay-later declined**
- Same as Test 2 but give device ID starting `test-adv-used-01`
- Agent should decline without saying why, still send the link
- **Expected mock hits:** `/devices/lookup`, `/advance` (declined: advance_used), `/payment-links`

**Test 4 — Device not found → screen check**
- "I'm at General Hospital", "Device ID test-404"
- Agent should run the device-not-found branch: "Is there anything showing on the screen?"
- Answer "no, it's black" → agent walks through cable check
- **Expected mock hits:** `/devices/lookup` (not found)

**Test 5 — Clinical emergency hard-stop**
- At any point during a call, say "I've fallen and need a nurse"
- Agent should immediately tell you to press the nurse call button and end the call
- No ticket should be logged

**Test 6 — Invoice copy**
- "I'm at General Hospital, device 86e7e12, I want a copy of my invoice from last week"
- Give a mobile, confirm, agent sends invoice SMS
- **Expected mock hits:** `/devices/lookup`, `/invoices/send-sms`

### What to watch for

- **Is the Find device call hitting the mock?** Check the uvicorn terminal — you should see `POST /hospitals/.../devices/lookup`. If not, the API URL or bearer isn't wired right.
- **Does the agent read back the mobile number** before sending SMS? (Required safeguard.)
- **Does the agent refuse card numbers by voice** if you try to read one?
- **Does the clinical escalation hard-stop actually end the call** without logging a ticket?
- **Does the agent say "the number ending in XXXX"** matching the last 4 you gave?

---

## Troubleshooting

| Symptom | Likely fix |
|---|---|
| Webhook nodes timing out | Mock isn't reachable. Check trycloudflare URL still works, uvicorn still running. |
| `401 unauthorized` in uvicorn logs | Bearer token mismatch. Confirm Bland secret matches `MOCK_BEARER` from run.sh. |
| Pathway never gets past "Find device" | API base URL in pathway JSON still says `REPLACE-WITH-LSP-API-BASE`. Re-run the sed. |
| Agent asks for device ID again and again | `device_found: false` response. Either you said `test-404`, or the hospital/device_id combo didn't match. Say "86e7e12" or similar. |
| Agent tries to transfer and fails | Expected in Voice Chat — transfer is a real phone action. Not a problem for POC. |
| Mock doesn't start | `./run.sh` needs Python 3.11+ (uses union-type syntax). On NixOS it uses `nix shell nixpkgs#python3` so should be fine. |

---

## What this POC does and doesn't prove

**Proves:**
- The pathway import works and the graph is wired correctly
- The 25 nodes, 3 global nodes and 35 routes behave as the PDF specifies
- The webhook contracts with LSPcare match the mock (and therefore the design doc)
- The conversation quality in Voice Chat feels natural enough to carry a real call
- The safety rails (clinical hard-stop, no card numbers, mobile read-back, one advance per stay) are actually enforced

**Does not prove:**
- That the real LSPcare API returns the same shapes as the mock (worth a separate check against the real API once we're cleared to hit it)
- Call quality over a real phone line — voice-chat-in-browser is forgiving
- Hospital list completeness, troubleshooting accuracy against the real device, transfer behaviour
- Resilience under real patient callers (confused, elderly, interrupting, non-English)

Treat this as the end of the "does the design work on paper" phase and the start of the "does the agent survive real use" phase.
