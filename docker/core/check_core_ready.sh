#!/usr/bin/env bash
# Read-only readiness check: the Core Portal accepts a TCP connection.
# It sends nothing and calls no Portal method.
set -euo pipefail
exec 3<> "/dev/tcp/127.0.0.1/${MIOS_WS_PORT:-12000}"
