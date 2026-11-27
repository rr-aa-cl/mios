#!/usr/bin/env bash
# Read-only Docker/Kubernetes readiness check; never calls controller services.
set -euo pipefail
marker="${MIOS_CONTROL_STATE_DIR:-/run/mios-control}/ready"
[[ -r "${marker}" ]] || exit 1
read -r pid start_time extra < "${marker}"
[[ "${pid}" =~ ^[1-9][0-9]*$ && "${start_time}" =~ ^[0-9]+$ && -z "${extra}" ]] || exit 1
[[ -r "/proc/${pid}/stat" ]] || exit 1
process_stat="$(< "/proc/${pid}/stat")"
read -r -a fields <<< "${process_stat##*) }"
[[ "${fields[0]}" != Z && "${fields[19]}" == "${start_time}" ]]
