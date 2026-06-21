@echo off
REM Install the AI Terminal Assistant on Windows.
REM Built by clavexis - github.com/clavexis
setlocal

echo ^>^> Installing Python dependencies...
python -m pip install -r "%~dp0requirements.txt"
if errorlevel 1 (
  echo Failed to install dependencies. Is Python 3 installed and on PATH?
  exit /b 1
)

echo.
echo ^>^> Done. Run the assistant with:
echo    python "%~dp0assistant.py" --set-key sk-ant-...
echo    python "%~dp0assistant.py"
echo.
echo Tip: create a shortcut or add a 'ai-assistant.bat' wrapper on your PATH
echo that calls:  python "%~dp0assistant.py" %%*
endlocal
