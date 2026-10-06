#!/usr/bin/env bash
# Run the Aqua deployment-verification smoke test unattended through the Aqua CLI.
#
# Sends "run the smoke test" in a new Aqua session, then "continue the smoke test" in the same
# session until Aqua's reply contains "SMOKE TEST COMPLETE" (or MAX_TURNS is reached). Every
# reply is saved under $OUT. Suitable for cron or CI.
#
# Needs: the Aqua CLI (https://get.codeocean.com/aqua-cli/) as `aqua` on PATH or in $AQUA,
#        python3, and CODEOCEAN_DOMAIN + CODEOCEAN_TOKEN (an API key) in the environment.
# Optional: MAX_TURNS (default 6), OUT (default ./smoke-<UTC time>),
#           AQ_CHECKS=1 to also ask the two section-8 questions that work without a page open,
#           each in a fresh session, and save the answers for a person to grade.
#
# Only the -json and -session flags are ever passed to the CLI. Prompts go on stdin.
# Exit code: 0 = complete, 3 = not complete after MAX_TURNS, 1 = CLI error.
set -euo pipefail

[ "$#" -eq 0 ] || { echo "usage: $0   (no arguments; settings come from the environment)" >&2; exit 2; }
AQUA="${AQUA:-aqua}"
MAX_TURNS="${MAX_TURNS:-6}"
OUT="${OUT:-smoke-$(date -u +%Y%m%dT%H%MZ)}"
: "${CODEOCEAN_DOMAIN:?set CODEOCEAN_DOMAIN}"
: "${CODEOCEAN_TOKEN:?set CODEOCEAN_TOKEN}"
command -v "$AQUA" >/dev/null || { echo "Aqua CLI not found (set AQUA=/path/to/aqua)" >&2; exit 1; }
mkdir -p "$OUT"

field() { python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))[sys.argv[2]])' "$1" "$2"; }

ask() {  # ask <turn-file-stem> <prompt> [session]
  local stem="$1" prompt="$2" session="${3:-}"
  if [ -n "$session" ]; then
    printf '%s\n' "$prompt" | "$AQUA" -json -session "$session" > "$OUT/$stem.json"
  else
    printf '%s\n' "$prompt" | "$AQUA" -json > "$OUT/$stem.json"
  fi
  field "$OUT/$stem.json" reply > "$OUT/$stem.md"
}

echo "$(date -u +%FT%TZ) starting smoke test on $CODEOCEAN_DOMAIN; replies in $OUT/"
ask turn-01 "run the smoke test" || { echo "Aqua CLI failed on turn 1" >&2; exit 1; }
SESSION="$(field "$OUT/turn-01.json" session_id)"
echo "$SESSION" > "$OUT/session_id.txt"

turn=1
status=3
while :; do
  if grep -q "SMOKE TEST COMPLETE" "$OUT/turn-$(printf %02d "$turn").md"; then status=0; break; fi
  [ "$turn" -lt "$MAX_TURNS" ] || break
  turn=$((turn + 1))
  echo "$(date -u +%FT%TZ) turn $turn: continue"
  ask "turn-$(printf %02d "$turn")" "continue the smoke test" "$SESSION" || { echo "Aqua CLI failed on turn $turn" >&2; exit 1; }
done

if [ "${AQ_CHECKS:-0}" = 1 ]; then
  ask aq-2 "List my 3 most recently accessed Capsules" || true
  ask aq-3 "What is a Data Asset?" || true
  echo "Section 8 answers saved to $OUT/aq-2.md and $OUT/aq-3.md for a person to grade (AQ-1 needs a capsule open in the web UI)."
fi

final="$OUT/turn-$(printf %02d "$turn").md"
cp "$final" "$OUT/final-reply.md"
echo "$(date -u +%FT%TZ) finished after $turn turn(s); final reply: $OUT/final-reply.md"
grep -E "SMOKE TEST (COMPLETE|INCOMPLETE)" "$final" || echo "(no summary line in the final reply)"
exit "$status"
