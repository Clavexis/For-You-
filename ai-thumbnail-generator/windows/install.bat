@echo off
REM Install AI Thumbnail Generator on Windows. Built by clavexis - github.com/clavexis
python -m pip install -r "%~dp0requirements.txt"
echo Installed. Try:  python "%~dp0thumbnail.py" "My Video Title" --style gaming
