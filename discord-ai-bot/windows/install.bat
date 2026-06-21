@echo off
REM Install Discord AI Bot on Windows. Built by clavexis - github.com/clavexis
python -m pip install -r "%~dp0requirements.txt"
echo ^>^> Installed. Copy config.json.example to config.json, add your tokens,
echo    then run:  python "%~dp0bot.py"
