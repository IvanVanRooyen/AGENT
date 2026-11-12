# AGENT

Working repository for LSP-related artefacts produced during career and engineering engagement planning.

## Monday 17 Nov 2026 — CEO meeting pack

The complete pack, in order of what to use when:

| File | Purpose |
|---|---|
| [`pdf/monday-proposal.pdf`](pdf/monday-proposal.pdf) | **Leave-behind.** One-page proposal + architecture appendix. Hand to CEO at end of meeting. |
| [`pdf/monday-poc-kit.pdf`](pdf/monday-poc-kit.pdf) | **Working document.** Demo script, printed backup pack (pages 1-4 of Part 2), likely CEO questions with pre-prepared answers, post-meeting follow-up email template. |
| [`monday-proposal.md`](monday-proposal.md) | Source markdown for the proposal. |
| [`monday-poc-kit.md`](monday-poc-kit.md) | Source markdown for the POC kit. |
| [`diagrams/`](diagrams/) | Mermaid source + rendered PNGs for all four architecture diagrams. |

## Diagrams

| File | Where it's used |
|---|---|
| `lsp-v1-architecture.png` | Proposal appendix — target state v1 architecture |
| `homelab-architecture.png` | POC kit Part 2 page 1 — current homelab three-layer stack |
| `alert-flow-sequence.png` | POC kit Part 2 page 2 — service down → SMS in hand round-trip |
| `homelab-to-lsp-mapping.png` | POC kit Part 2 page 4 — side-by-side mapping of components |

## Reference material

- `Software Design Document-NOT FINALIZED.pdf` — Saran Saravanan's January 2026 SDD for the LSP telemetry platform. Source document the Monday proposal responds to.
- `Customer Service and IT Support Job in Berrinba, Brisbane QLD - SEEK.pdf` — SEEK advert for the IT Support role Ivan declined (Nov 2026). Role-context for the side-of-desk framing.

## Rebuilding the PDFs

Toolchain: `pandoc` + `typst` for PDF, `mermaid-cli` for diagrams. On NixOS:

```bash
# Re-render diagrams from mermaid sources
cd diagrams
nix shell nixpkgs#mermaid-cli --command bash -c '
  for f in *.mmd; do
    mmdc -i "$f" -o "${f%.mmd}.png" -b white --scale 2 -p puppeteer-config.json
  done
'

# Render markdowns to PDF
cd ..
nix shell nixpkgs#pandoc nixpkgs#typst --command bash -c '
  pandoc monday-proposal.md --pdf-engine=typst -o pdf/monday-proposal.pdf
  pandoc monday-poc-kit.md  --pdf-engine=typst -o pdf/monday-poc-kit.pdf
'
```

If you edit the markdowns, re-run the second command. If you edit a diagram, re-run both.
