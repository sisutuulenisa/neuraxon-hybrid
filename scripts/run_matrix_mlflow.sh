#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
VENV_DIR="${REPO_ROOT}/.venv-mlflow-smoke"

if [[ ! -x "${VENV_DIR}/bin/python" ]]; then
  python3 -m venv "${VENV_DIR}"
fi

"${VENV_DIR}/bin/pip" install --quiet --disable-pip-version-check "mlflow-skinny==2.20.1"

exec "${VENV_DIR}/bin/python" "${REPO_ROOT}/scripts/run_matrix.py" --enable-mlflow "$@"
