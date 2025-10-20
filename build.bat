pyinstaller --noconsole --add-data "./ffmpeg;ffmpeg" whydiscordwhy.py --icon=icon.ico --noconfirm
xcopy venv\Lib\site-packages\tkinterdnd2 dist\whydiscordwhy\_internal\tkinterdnd2 /I /E
copy icon.ico dist\whydiscordwhy\icon.ico
copy cpu-theme.json dist\whydiscordwhy\cpu-theme.json
copy amd-theme.json dist\whydiscordwhy\amd-theme.json
copy nvidia-theme.json dist\whydiscordwhy\nvidia-theme.json
copy intel-theme.json dist\whydiscordwhy\intel-theme.json

copy config.json dist\whydiscordwhy\config.json