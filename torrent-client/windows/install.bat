@echo off
REM Install clawtorrent on Windows. Built by clavexis - github.com/clavexis
set "DEST=%USERPROFILE%\bin"
if not exist "%DEST%" mkdir "%DEST%"
copy /Y "%~dp0clawtorrent.py" "%DEST%\clawtorrent.py" >nul
echo Installed to %DEST%\clawtorrent.py (pure Python 3, no dependencies).
echo Run with:  python "%DEST%\clawtorrent.py" test
