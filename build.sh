#!/bin/bash
pyinstaller --noconsole whydiscordwhy.py --icon=icon.png --noconfirm
cp -r venv/lib/python3.13/site-packages/tkinterdnd2 dist/whydiscordwhy/_internal/tkinterdnd2
cp icon.png dist/whydiscordwhy/icon.png
cp theme.json dist/whydiscordwhy/theme.json
cp config.json dist/whydiscordwhy/config.json

