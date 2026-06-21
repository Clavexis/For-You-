@echo off
REM Install Password Manager on Windows. Built by clavexis - github.com/clavexis
python -m pip install -r "%~dp0requirements.txt"
echo Installed. Start with:  python "%~dp0vault.py" init
