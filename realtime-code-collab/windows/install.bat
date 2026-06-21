@echo off
REM Install Real-Time Code Collab on Windows. Built by clavexis - github.com/clavexis
python -m pip install -r "%~dp0requirements.txt" windows-curses
echo Installed. Start a server:  python "%~dp0collab.py" server
echo Then join:                  python "%~dp0collab.py" join myroom
endlocal
