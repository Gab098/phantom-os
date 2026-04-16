#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
VENV_PYTHON="${PROJECT_ROOT}/.venv/bin/python"
SERVER_LOG="${PROJECT_ROOT}/runtime/llm-server.log"
PORT=18080

if [[ ! -x "${VENV_PYTHON}" ]]; then
    echo "Missing virtualenv at ${PROJECT_ROOT}/.venv"
    echo "Run ./build/dev-setup.sh first."
    exit 1
fi

mkdir -p "${PROJECT_ROOT}/runtime"
rm -f "${SERVER_LOG}"

cleanup() {
    if [[ -n "${SERVER_PID:-}" ]]; then
        kill "${SERVER_PID}" >/dev/null 2>&1 || true
        wait "${SERVER_PID}" >/dev/null 2>&1 || true
    fi
}
trap cleanup EXIT

export PYTHONPATH="${PROJECT_ROOT}"
export PHANTOM_MODEL_PATH="${PROJECT_ROOT}/Qwen3.5-0.8B-BF16.gguf"

"${VENV_PYTHON}" "${PROJECT_ROOT}/ai/llm/llm_server.py" "${PHANTOM_MODEL_PATH}" "${PORT}" >"${SERVER_LOG}" 2>&1 &
SERVER_PID=$!

for _ in {1..60}; do
    if curl -fsS "http://127.0.0.1:${PORT}/health" \
        -o /dev/null 2>/dev/null; then
        break
    fi
    if ! kill -0 "${SERVER_PID}" 2>/dev/null; then
        echo "LLM server exited unexpectedly."
        cat "${SERVER_LOG}"
        exit 1
    fi
    sleep 1
done

RESPONSE="$(curl -fsS -X POST "http://127.0.0.1:${PORT}" \
    -H "Content-Type: application/json" \
    -d '{"prompt":"echo hello from phantom","max_tokens":32,"temperature":0.1}')"

echo "Server response: ${RESPONSE}"
echo "Health response: $(curl -fsS "http://127.0.0.1:${PORT}/health")"

"${VENV_PYTHON}" - <<'PY'
from ai.terminal.phantom_terminal import PhantomTerminal

terminal = PhantomTerminal()
terminal.server_port = 18080
terminal.server_url = "http://127.0.0.1:18080"
command = terminal.natural_to_bash("list the current directory")
print(f"Terminal command: {command}")
assert command and isinstance(command, str)
PY

echo "Smoke test passed."
