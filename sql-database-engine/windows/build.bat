@echo off
REM Build the SQL engine on Windows. Built by clavexis - github.com/clavexis
REM Uses POSIX-ish calls; build under WSL with the linux/ Makefile, or MinGW gcc.
where gcc >nul 2>nul && ( gcc -O2 -o db.exe "%~dp0db.c" && echo Built db.exe & goto :eof )
echo Build under WSL (recommended): cd linux ^&^& make
