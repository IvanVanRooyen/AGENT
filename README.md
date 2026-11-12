# AGENT

Working repository for LSP-related artefacts produced during career/engineering engagement planning.

## Contents

### Monday 17 Nov 2026 — CEO meeting on telemetry scope
- [`monday-proposal.md`](monday-proposal.md) — one-page, PDF-ready side-of-desk proposal (the leave-behind).
- [`monday-poc-kit.md`](monday-poc-kit.md) — live demo script + 4-page printed backup pack + pre-meeting checklist.

### Reference material
- `Software Design Document-NOT FINALIZED.pdf` — Saran Saravanan's January 2026 SDD for the LSP telemetry platform. Source document the Monday proposal responds to.
- `Customer Service and IT Support Job in Berrinba, Brisbane QLD - SEEK.pdf` — SEEK advert for the IT Support role Ivan declined (Nov 2026). Role-context for the side-of-desk framing.

## Rendering the proposal to PDF

```bash
pandoc monday-proposal.md -o monday-proposal.pdf \
  --pdf-engine=xelatex \
  -V geometry:margin=1.8cm \
  -V fontsize=11pt
```

Adjust margin or font size if it spills past one page on your renderer.
