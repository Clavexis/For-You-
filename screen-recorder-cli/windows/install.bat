@echo off
REM Install Screen Recorder CLI on Windows. Built by clavexis - github.com/clavexis
where ffmpeg >nul 2>nul || echo Note: install ffmpeg first:  winget install Gyan.FFmpeg
echo Run:  python "%~dp0screenrec.py" out.mp4 --duration 10
