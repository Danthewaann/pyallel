#!/bin/sh
# Simple wrapper around pyinstaller

set -e

# Use the hacked ldd to fix libc.musl-x86_64.so.1 location
PATH="/pyinstaller:$PATH"

pip install .

# Exclude pycrypto and PyInstaller from built packages
pyinstaller \
    --onefile \
    --noconfirm \
    --clean \
    --log-level DEBUG \
    --exclude-module PyInstaller \
    --copy-metadata pyallel \
    --name pyallel-0.18.5-alpine-x86_64 \
    ./src/pyallel/main.py
