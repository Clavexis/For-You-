@echo off
REM Install AI Commit Writer on Windows. Built by clavexis - github.com/clavexis
python -m pip install -r "%~dp0requirements.txt"
echo Installed. In any git repo:  git add .  ^&^&  python "%~dp0aicommit.py" --commit
