#!/usr/bin/env sh
set -eu

usage() {
  cat >&2 <<'USAGE'
Usage:
  inject_fault.sh netem_delay <container> <delay_ms> [jitter_ms] [timeline_jsonl]
  inject_fault.sh netem_loss <container> <loss_percent> [timeline_jsonl]
  inject_fault.sh pause_container <container> <duration_seconds> [timeline_jsonl]
USAGE
  exit 2
}

json_escape() {
  printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'
}

write_event() {
  status="$1"
  detail="$2"
  ts="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  mkdir -p "$(dirname "$TIMELINE")"
  printf '{"timestamp":"%s","action":"%s","target":"%s","status":"%s","detail":"%s"}\n' \
    "$ts" "$(json_escape "$ACTION")" "$(json_escape "$TARGET")" "$(json_escape "$status")" "$(json_escape "$detail")" >> "$TIMELINE"
}

if [ "$#" -lt 2 ]; then
  usage
fi

ACTION="$1"
TARGET="$2"
shift 2
TIMELINE="${RUN_DIR:-./data/runs/manual}/evidence/fault_timeline.jsonl"

case "$ACTION" in
  netem_delay)
    if [ "$#" -lt 1 ]; then usage; fi
    DELAY_MS="$1"
    JITTER_MS="${2:-0}"
    if [ "$#" -ge 3 ]; then TIMELINE="$3"; fi
    docker exec "$TARGET" sh -c "tc qdisc replace dev eth0 root netem delay ${DELAY_MS}ms ${JITTER_MS}ms"
    write_event "applied" "tc qdisc replace dev eth0 root netem delay ${DELAY_MS}ms ${JITTER_MS}ms"
    ;;
  netem_loss)
    if [ "$#" -lt 1 ]; then usage; fi
    LOSS_PERCENT="$1"
    if [ "$#" -ge 2 ]; then TIMELINE="$2"; fi
    docker exec "$TARGET" sh -c "tc qdisc replace dev eth0 root netem loss ${LOSS_PERCENT}%"
    write_event "applied" "tc qdisc replace dev eth0 root netem loss ${LOSS_PERCENT}%"
    ;;
  pause_container)
    if [ "$#" -lt 1 ]; then usage; fi
    DURATION_SECONDS="$1"
    if [ "$#" -ge 2 ]; then TIMELINE="$2"; fi
    docker pause "$TARGET"
    write_event "paused" "docker pause for ${DURATION_SECONDS}s"
    sleep "$DURATION_SECONDS"
    docker unpause "$TARGET"
    write_event "unpaused" "docker unpause after ${DURATION_SECONDS}s"
    ;;
  *)
    usage
    ;;
esac
