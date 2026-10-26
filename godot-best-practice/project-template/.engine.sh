#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${ROOT}"
if [[ $# -eq 0 ]]; then
    exec python3 .engine_host.py run --editor --path "${ROOT}"
fi
exec python3 .engine_host.py run "$@"
