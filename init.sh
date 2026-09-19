#!/usr/bin/env bash

set -u

ok() { printf "[OK]    %s\n" "$1"; }
warn() { printf "[WARN]  %s\n" "$1"; }
fail() { printf "[FAIL]  %s\n" "$1"; }

EXIT_CODE=0
PYTHON_CMD=""

echo "== 1. Entorno =="

for candidate in python python3 py; do
  if command -v "$candidate" >/dev/null 2>&1; then
    PYTHON_CMD="$candidate"
    break
  fi
done

if [ -z "$PYTHON_CMD" ]; then
  fail "No se encontro Python. Instala Python 3.9+ y agregalo al PATH."
  exit 1
fi

ok "Python -> $($PYTHON_CMD --version)"

$PYTHON_CMD - <<'PY'
import sys

if sys.version_info < (3, 9):
    print("[FAIL]  Se requiere Python >= 3.9")
    raise SystemExit(1)

print("[OK]    Version de Python compatible")
PY

if [ $? -ne 0 ]; then
  exit 1
fi

echo ""
echo "== 2. Archivos base =="

for file in \
  AGENTS.md \
  init.sh \
  progress/history.md \
  docs/architecture.md \
  docs/conventions.md \
  docs/verification.md \
  openspec/config.yaml
do
  if [ -f "$file" ]; then
    ok "Existe $file"
  else
    fail "Falta $file"
    EXIT_CODE=1
  fi
done

echo ""
echo "== 3. Tests =="

"$PYTHON_CMD" - <<'PY'
from pathlib import Path
import sys
import unittest

if not Path("tests").is_dir():
    print("[WARN]  No existe tests/")
else:
    suite = unittest.defaultTestLoader.discover("tests")
    if suite.countTestCases() == 0:
        print("[WARN]  No hay tests todavia")
    else:
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        if not result.wasSuccessful():
            raise SystemExit(1)
        print("[OK]    Tests pasan")
PY

if [ $? -ne 0 ]; then
  fail "Fallo al descubrir o ejecutar tests"
  EXIT_CODE=1
fi

echo ""
echo "== 4. Resumen =="

if [ $EXIT_CODE -eq 0 ]; then
  ok "Harness listo"
else
  fail "Harness no esta listo"
fi

exit $EXIT_CODE
