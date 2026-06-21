@echo off
REM Install P2P File Sharing on Windows. Built by clavexis - github.com/clavexis
python -m pip install -r "%~dp0requirements.txt"
echo Installed. Send:  python "%~dp0p2p.py" send file.zip
echo Receive:           python "%~dp0p2p.py" recv HOST PORT CODE
