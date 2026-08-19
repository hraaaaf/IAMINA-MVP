#!/bin/bash
cd "$(dirname "$0")" || exit 1
python3 ./IAMINA.py "$@"
status=$?
if [ "$status" -ne 0 ] && [ -z "${CI:-}" ]; then
  printf '\nIAMINA failed (exit %s). Press Enter to close...' "$status"
  read -r _
fi
exit "$status"
