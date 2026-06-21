@echo off
REM Install clawfmt on Windows. Built by clavexis - github.com/clavexis
set "DEST=%USERPROFILE%\bin"
if not exist "%DEST%" mkdir "%DEST%"
copy /Y "%~dp0clawfmt.py" "%DEST%\clawfmt.py" >nul
echo Installed to %DEST%\clawfmt.py (pure Python 3, no dependencies).
echo Run with:  python "%DEST%\clawfmt.py" test
