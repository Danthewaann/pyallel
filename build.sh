#!/bin/sh

distro="${1:-linux}"

# Exclude PyInstaller from built packages
pyinstaller \
    --onefile \
    --noconfirm \
    --clean \
    --log-level DEBUG \
    --exclude-module PyInstaller \
    --copy-metadata pyallel \
    --name pyallel-"$(pyallel -v)"-"$distro"-x86_64 \
    ./src/pyallel/main.py
