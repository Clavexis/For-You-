@echo off
REM Install Terminal Music Player on Windows. Built by clavexis - github.com/clavexis
python -m pip install -r "%~dp0requirements.txt"
echo Installed. Configure Spotify credentials (see README), then:
echo    python "%~dp0player.py" now
