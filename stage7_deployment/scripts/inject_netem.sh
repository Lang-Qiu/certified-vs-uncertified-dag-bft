#!/usr/bin/env bash
set -euo pipefail

IFACE="${IFACE:-eth0}"
DELAY_MS="${NETEM_DELAY_MS:-0}"
JITTER_MS="${NETEM_JITTER_MS:-0}"
LOSS_PCT="${NETEM_LOSS_PCT:-0}"

die() {
  echo "error: $*" >&2
  exit 1
}

require_uint() {
  local name="$1"
  local value="$2"
  [[ "$value" =~ ^[0-9]+$ ]] || die "$name must be a non-negative integer; got '$value'"
}

require_number() {
  local name="$1"
  local value="$2"
  [[ "$value" =~ ^[0-9]+([.][0-9]+)?$ ]] || die "$name must be a non-negative number; got '$value'"
}

[[ "$IFACE" =~ ^[A-Za-z0-9_.:-]+$ ]] || die "IFACE contains unsupported characters; got '$IFACE'"
require_uint "NETEM_DELAY_MS" "$DELAY_MS"
require_uint "NETEM_JITTER_MS" "$JITTER_MS"
require_number "NETEM_LOSS_PCT" "$LOSS_PCT"

tc qdisc del dev "$IFACE" root 2>/dev/null || true

if [[ "$DELAY_MS" == "0" && "$JITTER_MS" == "0" && "$LOSS_PCT" == "0" ]]; then
  echo "netem cleared on $IFACE"
  tc qdisc show dev "$IFACE"
  exit 0
fi

tc qdisc add dev "$IFACE" root netem delay "${DELAY_MS}ms" "${JITTER_MS}ms" loss "${LOSS_PCT}%"
tc qdisc show dev "$IFACE"
