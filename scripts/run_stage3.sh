'''!/usr/bin/env bash'''
set -e

echo "=== minimal VFS ==="
python src/emulator.py --vfs vfs/minimal.csv --script start_scripts/start_stage1.txt

echo "=== files VFS ==="
python src/emulator.py --vfs vfs/files.csv --script start_scripts/start_stage3.txt

echo "=== deep VFS (3+ levels) ==="
python src/emulator.py --vfs vfs/deep.csv --script start_scripts/start_stage3.txt
