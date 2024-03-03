#!/bin/sh

distro="${1:-linux}"

# --bootloader-ignore-signals is needed as two interrupt signals where getting sent
# to pyallel as it is apart of the same process group as the bootloader
# From: https://pyinstaller.org/en/stable/usage.html#cmdoption-bootloader-ignore-signals
pyinstaller \
    --onefile \
    --noconfirm \
    --clean \
    --log-level DEBUG \
    --exclude-module PyInstaller \
    --copy-metadata pyallel \
    --bootloader-ignore-signals \
    --name pyallel-"$(pyallel -v)"-"$distro"-x86_64 \
    ./src/pyallel/main.py
