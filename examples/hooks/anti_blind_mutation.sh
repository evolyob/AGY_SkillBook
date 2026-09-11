#!/bin/bash
# Backward-compatibility wrapper delegating to anti_blind_mutation.py
exec python3 "$(dirname "$0")/anti_blind_mutation.py"
