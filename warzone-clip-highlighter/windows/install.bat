@echo off
REM Install Warzone Clip Highlighter on Windows. Built by clavexis - github.com/clavexis
where ffmpeg >nul 2>nul || echo Note: install ffmpeg first:  winget install Gyan.FFmpeg
echo Run:  python "%~dp0highlighter.py" gameplay.mp4 -o highlights.mp4
