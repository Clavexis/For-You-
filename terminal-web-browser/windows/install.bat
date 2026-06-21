@echo off
REM Install clawbrowse on Windows. Built by clavexis - github.com/clavexis
set "DEST=%USERPROFILE%\bin"
if not exist "%DEST%" mkdir "%DEST%"
copy /Y "%~dp0clawbrowse.py" "%DEST%\clawbrowse.py" >nul
echo Installed to %DEST%\clawbrowse.py (pure Python 3, no dependencies).
echo Run with:  python "%DEST%\clawbrowse.py" https://example.com
