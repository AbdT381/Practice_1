'''!/usr/bin/env bash'''
set -e
python src/emulator.py --vfs vfs/files.csv --script start_scripts/start_stage2.txt
