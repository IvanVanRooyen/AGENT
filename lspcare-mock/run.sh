#!/usr/bin/env bash
# Run the LSPcare mock locally, expose via Cloudflare quick tunnel (trycloudflare.com),
# and print the public URL + bearer token to paste into the Bland pathway.
#
# Prereqs: nothing installed globally — uses nix shell for everything.

set -euo pipefail
cd "$(dirname "$0")"

MOCK_BEARER="${MOCK_BEARER:-$(head -c 24 /dev/urandom | od -An -tx1 | tr -d ' \n')}"
export MOCK_BEARER

echo
echo "=== LSPcare mock ==="
echo "Bearer token: $MOCK_BEARER"
echo "(copy this; you'll paste it into the Bland pathway's Authorization header)"
echo
echo "Starting mock on :8099 and opening a trycloudflare.com tunnel..."
echo

exec nix shell nixpkgs#python3 nixpkgs#cloudflared --command bash -c '
  python3 -m venv .venv 2>/dev/null || true
  source .venv/bin/activate
  pip install -q -r requirements.txt

  # Start uvicorn in the background
  uvicorn main:app --host 127.0.0.1 --port 8099 &
  UVICORN_PID=$!
  trap "kill $UVICORN_PID 2>/dev/null || true" EXIT

  sleep 2
  echo
  echo "=== Cloudflare tunnel starting ==="
  echo "Watch for the trycloudflare.com URL below — paste it into the Bland pathway."
  echo
  cloudflared tunnel --no-autoupdate --url http://127.0.0.1:8099
'
