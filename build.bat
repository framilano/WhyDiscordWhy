pyinstaller --noconsole --add-data "./ffmpeg;ffmpeg" whydiscordwhy.py --icon=icon.ico --noconfirm
xcopy venv\Lib\site-packages\tkinterdnd2 dist\whydiscordwhy\_internal\tkinterdnd2 /I /E
copy icon.ico dist\whydiscordwhy\icon.ico
copy theme.json dist\whydiscordwhy\theme.json
copy config.json dist\whydiscordwhy\config.json