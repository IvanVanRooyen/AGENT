---
name: ""
metadata: 
  node_type: memory
  title: LSP Telemetry — Side-of-Desk Proposal
  author: Ivan Van Rooyen
  date: 17 November 2026
  geometry: margin=1.8cm
  fontsize: 11pt
  mainfont: Inter
  originSessionId: 5ef4c2ce-e09c-4a07-b24c-f109c31ab290
---

# LSP Telemetry — Side-of-Desk Proposal

**Ivan Van Rooyen · 17 November 2026**

## Arrangement

I continue as Sales & Project Specialist at my current salary. The telemetry system becomes a parallel engineering engagement I own, scoped to ~10 focused hours a week. No role transition, no pay change — LSP gets the system built; I keep the engineering output on my record.

## What the system is for

> **"Know about customer-visible problems before the customer notices."**

That reframes this from an infrastructure-telemetry project into an **incident detection and response system** for support staff and management. WiFi down at a site, a bed terminal unreachable, an LSPcare instance throwing errors — we hear about it from our own system, not from the customer's call.

## v1 — minimum viable incident detection

Four components, deliverable in a single pilot slice:

1. **Per-site endpoint probes.** Uptime Kuma (or equivalent) runs synthetic checks against each site's public-facing and internal endpoints — HTTP health, ping, TCP reachability. One central instance polls every site over existing VPN / Tailscale.
2. **Status board.** A single dashboard that answers "what's broken right now, which customer is affected, since when." Not analytical — operational.
3. **SMS alerting.** Twilio-based, routed to the on-call support staff. Same pattern I already run in production at home (see POC pack).
4. **Zoho Desk auto-ticketing** via a pluggable integration layer. When an incident fires, a ticket is created with context. If LSP ever changes ticketing systems, the integration is reconfigured — not rebuilt.

## v2 — after v1 proves value

- **Stale-ticket escalator.** Polls Zoho Desk, SMSes the responsible support staff when a ticket passes its SLA window without activity. Thresholds configurable per severity.
- **Infrastructure metrics layer.** Prometheus + VictoriaMetrics + Grafana as a *second* tier for post-incident investigation. This is Saran's original design, preserved and demoted — useful once v1 is detecting incidents, not required to detect them.
- **Multi-tenant / per-customer views** if the business asks for them.

## Capacity and timeline

- **~8–12 hours per week** as a realistic side-of-desk engagement.
- **6–9 month target** to ship v1 across 10–20 sites — hotels first (lower stakes), then hospitals. The original design targeted 60+ sites and 1M metrics/min; that ambition isn't dropped, it just belongs after v1 is proven.
- **No commitment today.** Walking out of this meeting I'll come back with a written scope and milestone plan if we're aligned.

## What I'd need from LSP

- **Connectivity** — read-only VPN/Tailscale reachability from a central point to each pilot site, or a lightweight prober installed per site that phones home.
- **Zoho Desk API credentials** and a list of must-have v1 signals (WiFi reachability, LSPcare HTTP uptime, bed terminal ping — your call on priority).
- **Modest cloud budget** — single VPS (~$20–40/month) and Twilio SMS volume. Breakdown on request.
- **Portfolio rights** — permission to write about the architecture and outcomes publicly, within commercial-sensitivity limits we agree on.

## Proof this isn't theoretical

I already run this exact pattern at home — Uptime Kuma + Grafana Alerting + a Twilio SMS bridge I wrote in Node.js, protected by sops-nix secrets management, monitoring 11 services and 2 hosts with 14 alert rules. Live demo and printed walkthrough available in this meeting.
