# LSPcare Support – Bland AI build pack

Everything Bland needs to build the LSPcare Support phone agent.

## Files

| File | What it is | Where it goes in Bland |
| --- | --- | --- |
| `lspcare-support-pathway.json` | The full conversational pathway: 25 nodes, 3 global nodes, 35 routes, and the global prompt | Pathway API (Update Pathway body), or give to Bland to import |
| `global-prompt.txt` | Rules for every node (tone, safety, payments) | Pathway › Global Prompt (already inside the JSON) |
| `knowledge-base.txt` | FAQ, prices, troubleshooting, hospital list | Knowledge › Upload Text (also pasted into the two Knowledge Base nodes) |

## Import

1. In Bland, create an empty pathway called **LSPcare Support** and copy its pathway ID.
2. Send `lspcare-support-pathway.json` as the body of the **Update Pathway** API call for that ID (header `authorization: <Bland API key>`), or ask your Bland contact to import it.
3. Open the pathway in the editor and check each Webhook node's response routing displays correctly (see "Check after import").
4. Buy or attach the inbound number, attach the pathway, and set the post-call webhook (below).

## Replace before testing

| Placeholder | Where | Replace with |
| --- | --- | --- |
| `https://REPLACE-WITH-LSP-API-BASE` | Webhook nodes 3, 7b, 8, 10b, 12b | LSPcare API base URL |
| Authorization | Webhook nodes | Bearer token stored in Bland Secrets (add in each Webhook node's auth setting) |
| `+61000000000` | Node 10c Transfer to Helpdesk | Helpdesk transfer number (TBD) |
| `[REPLACE WITH LSP'S HOSPITAL LIST]` | `knowledge-base.txt` | Hospitals and the short names callers use |
| Troubleshooting steps | `knowledge-base.txt` | Confirm against the real screen and remote (written as a starting point) |

## LSPcare API the pathway calls

All `POST`, JSON in and out. Values in `{{ }}` are filled by Bland.

**1. Find device** – node 3 – `/hospitals/{hospital}/devices/lookup`

```json
// request
{"hospital": "{{hospital}}", "device_id": "{{device_id}}", "bed_id": "{{bed_id}}", "call_id": "{{call_id}}"}
// response
{"device_found": true, "device_id": "86e7e12", "package_active": false, "ends_at": null,
 "payment_pending_minutes": null, "advance_used": false, "balance_owing": false,
 "helpdesk_open": true}
```

**2. Pay-later check** – node 7b – `/devices/{device_id}/advance`
LSPcare decides; the agent only reads the answer. Approve only if: device found, no active package, no payment loading, no earlier advance this stay, no unpaid earlier advance, pay-by within 24 hours. The patient or a family member may request it. No cap on how many patients per hospital. If approved, switch on a 1 Day package. If an advance goes unpaid, block new purchases on that device until it is paid. Reason codes: `unpaid_advance`, `advance_used`, `package_active`, `payment_loading`, `device_not_found`.

```json
// request
{"hospital": "...", "device_id": "...", "bed_id": "...", "contact_name": "...", "mobile": "...",
 "email": "...", "pay_by": "tomorrow 10am", "call_id": "..."}
// response
{"approved": true, "reason": null, "ends_at": "Sat 1 Nov, 10:15 AM"}
// declined example
{"approved": false, "reason": "unpaid_advance", "ends_at": null}
```

**3. Send payment link by SMS** – node 8 – `/payment-links`
Texts a tv.lsp.io link with hospital and Device ID pre-filled, plus the pay-by time.

```json
// request
{"mobile": "...", "hospital": "...", "device_id": "...", "pay_by": "...", "advance_granted": "true", "call_id": "..."}
// response
{"sms_sent": true, "mobile_last4": "1234"}
```

**4. Log ticket** – node 10b – `/tickets`

```json
// request
{"hospital": "...", "device_id": "...", "bed_id": "...", "contact_name": "...", "mobile": "...",
 "callback_time": "...", "reason": "...", "intent": "...", "call_id": "...",
 "port_label": "9NE 092", "screen_state": "black", "screen_description": "..."}
// response
{"ticket_id": "LSP-10482"}
```

**5. Send invoice by SMS** – node 12b – `/invoices/send-sms`
Finds the matching purchase(s) on that device and texts a secure link to each invoice. The invoice shows package, amount, GST, date, hospital and Device ID; no card details beyond the last 4 digits. Links should expire (suggest 7 days).

```json
// request
{"hospital": "...", "device_id": "...", "invoice_period": "most recent", "invoice_package": "1 Week",
 "mobile": "...", "call_id": "..."}
// response
{"invoice_sent": true, "invoice_count": 1, "mobile_last4": "1234"}
```

## Helpdesk hours

Manned Monday to Friday, 8:30 am to 5:00 pm Brisbane time (AEST, UTC+10, no daylight saving). The Find device call returns `helpdesk_open`, worked out by LSPcare from the Brisbane clock, so the agent only offers a live transfer when the team is there. Outside hours, including weekends, it logs a callback for the next business day. Remember the NSW, VIC and other daylight-saving states are an hour ahead of Brisbane in summer.

## Post-call webhook

Inbound number › Advanced › Webhook: point to LSP's helpdesk system (still to be chosen). Bland sends the summary, transcript, extracted variables, disposition and recording URL after every call.

Suggested dispositions: `resolved`, `link_sent`, `invoice_sent`, `advance_granted`, `advance_declined`, `callback`, `transferred`, `clinical_redirect`, `device_not_found`.

## Check after import

- **Webhook routing:** nodes 3, 7b and 8 route on a response value (`device_found`, `advance_granted`, `sms_sent` equal to `true`); anything else takes the default route. Confirm these rules show in each node's Response Pathways panel.
- **SMS:** sent through LSP's own SMS gateway via `/payment-links`. No Bland SMS number is needed.
- **Recording:** all calls are recorded and the greeting says so.

## Test calls (Bland Unit Testing / Voice Chat)

| # | Scenario | Expected |
| --- | --- | --- |
| 1 | Asks how to buy | Steps from the knowledge base, offers SMS link |
| 2 | No card, first time, gives name, mobile, pays tomorrow 10am | 1 Day switched on, SMS sent, reference given |
| 3 | No card, already used pay-later this stay | Declined without reason, SMS link still sent |
| 4 | No card, won't give a mobile | Cannot grant, offers callback |
| 5 | Paid 2 minutes ago | Told to wait up to 5 minutes, not to pay again |
| 6 | Paid 15 minutes ago, still not working | Ticket logged, callback or transfer |
| 7 | Device not found, screen shows the home screen | Caller reads the bed number; lookup retried |
| 7b | Device not found, screen is black, cable was loose | Cable pushed into LSP-TV socket, screen back, call continues |
| 7c | Device not found, screen still black | Fault ticket with the socket label (e.g. 9NE 092) |
| 8 | "I've fallen and need a nurse" | Told to press nurse call button, call ends |
| 9 | Asks for a person at 2 pm Brisbane time | Offered a transfer now |
| 9b | Asks for a person on Friday at 7 pm Brisbane time | Callback logged for Monday |
| 11 | Family member calls, patient has no card | Pay-later offered; SMS to the family member's mobile |
| 13 | Wants a copy of last week's invoice | Confirms mobile, SMS invoice link sent |
| 14 | Wants an invoice, no purchase found | Offered a callback |
| 12 | No card, earlier pay-later unpaid | Told the earlier amount must be paid first; SMS link sent |
| 10 | Tries to read out card number | Agent stops them, offers SMS link |
