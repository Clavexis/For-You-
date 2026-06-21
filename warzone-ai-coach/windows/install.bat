@echo off
REM Install Warzone AI Coach on Windows. Built by clavexis - github.com/clavexis
setlocal
echo ^>^> Installing dependencies (anthropic SDK optional, enables AI coaching)...
python -m pip install -r "%~dp0requirements.txt"
echo.
echo ^>^> Done. Try:
echo    python "%~dp0coach.py" --stats "%~dp0sample-stats.json"
endlocal
