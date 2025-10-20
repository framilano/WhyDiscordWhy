#!/bin/bash
pyinstaller --noconsole whydiscordwhy.py --icon=icon.png --noconfirm
cp -r venv/lib/python3.13/site-packages/tkinterdnd2 dist/whydiscordwhy/_internal/tkinterdnd2
cp icon.png dist/whydiscordwhy/icon.png
cp cpu-theme.json dist/whydiscordwhy/cpu-theme.json
cp amd-theme.json dist/whydiscordwhy/amd-theme.json
cp nvidia-theme.json dist/whydiscordwhy/nvidia-theme.json
cp intel-theme.json dist/whydiscordwhy/intel-theme.json

cp config.json dist/whydiscordwhy/config.json

