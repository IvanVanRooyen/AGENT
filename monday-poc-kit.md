# Monday POC Kit — Homelab Proof-of-Concept

_Last modified: 2026-11-13_

Purpose: material to bring into the CEO meeting on 17 Nov 2026 to prove the v1 LSP telemetry architecture is already running as a working system at home. Two tracks — **live demo** (if connectivity and time allow) and **printed backup pack** (always have, hand over at the end).

---

## Track 1 — Live demo (5 minutes, laptop + hotspot)

Target flow: open three tabs, trace one alert end to end, close with the code.

### Pre-meeting checklist (do the evening before)

- [ ] Open the three target URLs on the laptop and leave tabs loaded: Uptime Kuma (`:3002`), Grafana Alerting (`:3000/alerting/list`), status page / dashboard view.
- [ ] Confirm all 11 Uptime Kuma monitors green — if anything is red, either fix it or use it as the demo incident.
- [ ] Phone hotspot tested and tethered laptop can reach the services (Tailscale is the clean path — confirm `tailscale status` on the laptop shows `nixos` as reachable).
- [ ] Phone with SIM in it — the Twilio alerts land on +61450264544. Put it on the table.
- [ ] USB drive with a PDF export of the printed pack as a fallback-fallback.

### Demo script

1. **Open with the frame, not the tech.** *"This is the same stack I'm proposing for LSP v1, running in my home environment for about a month. Let me trace one alert."*
2. **Tab 1 — Uptime Kuma.** Show the 11 monitors list. Point out: HTTP checks against real services (Plex, Immich, Firefly, BookStack), TCP checks against databases, 60s interval, alert after 3 consecutive failures. *"This is what each LSP site becomes in v1 — one row per endpoint we care about."*
3. **Tab 2 — Grafana Alerting.** Show the 10 configured rules across Host Health, Systemd Units, Proxmox Health. Click into one — e.g. "NAS Mount Gone" — show the Prometheus query and the 3-minute sustained condition. *"This is the second-tier layer — Saran's design, demoted to post-incident investigation."*
4. **Trigger an alert (optional, high impact).** If you can afford the time, deliberately stop a non-critical service (`systemctl --user stop sunshine.service`) and show the SMS arriving on the phone within ~3 minutes. Only do this if the first 3 minutes of the meeting went well and you have the slack.
5. **Tab 3 — the bridge code.** Open `~/nixos-config/scripts/grafana-twilio-bridge.js` in a terminal. *"This is ~40 lines of Node.js — it takes Grafana's webhook JSON and posts to the Twilio API. It's wrapped in a systemd service with sops-nix credentials. Same pattern is what plumbs the Zoho Desk integration in LSP v1 — just a different downstream."*
6. **Close.** *"Nothing in the v1 proposal needs to be invented. It's this stack, repointed at LSP endpoints, with Zoho Desk as a second downstream next to Twilio."*

### Known risks

- **Berrinba WiFi may not route to Tailscale** → use phone hotspot, don't rely on their network.
- **If a service is genuinely down at demo time** → turn it into the demo. Show the alert that fired.
- **If the laptop fails entirely** → the printed pack covers everything the live demo shows.

---

## Track 2 — Printed backup pack (leave-behind, 4 pages)

Print double-sided on good paper. Staple top-left. The CEO keeps this.

### Page 1 — Architecture diagram

One diagram showing the three layers and the SMS flow. Text-art version for sketching:

```
┌─────────────────────────────┐   ┌──────────────────────────────┐
│  Uptime Kuma (service probe)│   │ Prometheus + Grafana (host)  │
│  11 HTTP/TCP monitors       │   │ 10 alert rules, 2 hosts      │
└──────────────┬──────────────┘   └──────────────┬───────────────┘
               │                                 │
               │ native Twilio                   │ webhook → bridge (:9001)
               ▼                                 ▼
          ┌────────────────────────────────────────────┐
          │  Twilio REST API (credentials in sops-nix) │
          └──────────────────┬─────────────────────────┘
                             ▼
                       SMS → on-call
                             +
          ┌──────────────────────────────────────────┐
          │  Proxmox cron — cross-device ping        │
          │  UptimeRobot — external HTTP watchdog    │
          └──────────────────────────────────────────┘
```

Caption: *"For LSP v1, the Prometheus/Grafana layer is deferred to v2 and a Zoho Desk integration sits in parallel to Twilio on the output side."*

### Page 2 — Alert inventory (shows depth of coverage)

Table — copy from `service-alerting/INDEX.md` INDEX:

| Layer | Target | Rule |
|---|---|---|
| Uptime Kuma | Plex, Immich, Grafana, Prometheus, Firefly, BookStack, Overseerr, qBittorrent, Audiobookshelf, Postgres, MariaDB | HTTP/TCP, 3 consecutive fails ≈ 3 min |
| Grafana (NixOS) | Disk >90%, NAS mount gone, CPU >85°C, NVMe >70°C, cloudflared down, tailscaled down | 2–5 min sustained |
| Grafana (Proxmox) | k10temp >70°C, disk >90%, TrueNAS VM down, memory >90% | 3–5 min sustained |
| Proxmox cron | Server-down detection (ping fails 3× every 3 min) | ~9 min to SMS |
| UptimeRobot | External HTTP watchdog on public hostname | 5 min check |

### Page 3 — Bridge code snippet

Print `grafana-twilio-bridge.js` — the actual script. Pre-check before printing: strip any secrets if present (they should be loaded via `LoadCredential`, not hardcoded). Annotate the systemd unit wrapper briefly — DynamicUser, LoadCredential from `/run/secrets/`.

### Page 4 — Mapping to LSP v1

Side-by-side table:

| Homelab component | LSP v1 equivalent |
|---|---|
| Uptime Kuma monitoring 11 services | Uptime Kuma monitoring per-site endpoints (WiFi gateway, LSPcare HTTP, bed terminals) |
| Grafana Alerting (10 rules, 2 hosts) | Deferred to v2 — post-incident investigation layer |
| Twilio SMS bridge (Node.js) | Same bridge, Twilio downstream unchanged |
| sops-nix secrets | Same pattern — credentials never in git |
| Single Twilio number | Pluggable: SMS to on-call, Zoho Desk ticket in parallel |
| 1 home, 1 Proxmox host | 10–20 sites in pilot, extending to 60+ in v2+ |

Footer on page 4: *"Everything in LSP v1 is this stack, repointed and re-wrapped. The novel engineering is the Zoho Desk integration and the per-site onboarding flow — not the monitoring core."*

---

## Operational notes

- Don't print anything with credentials, tokens, or private IPs beyond the 192.168.4.x subnet. Numbers like `+12513130207` and `+61450264544` are fine to mention verbally but shouldn't be in the printed pack.
- Keep the whole pack to 4 pages max. The one-page proposal is the leave-behind that gets *acted on*; this pack is the backup that gets *filed*.
- If the meeting runs short, drop the live demo entirely — the proposal + printed pack is sufficient. If it runs long, the live demo is the memorable part they'll quote back.
