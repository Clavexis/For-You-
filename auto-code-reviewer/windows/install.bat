@echo off
REM Install Auto Code Reviewer on Windows. Built by clavexis - github.com/clavexis
setlocal
python -m pip install -r "%~dp0requirements.txt"
echo ^>^> Installed. Set ANTHROPIC_API_KEY, then:
echo    python "%~dp0review.py" yourfile.py
endlocal
