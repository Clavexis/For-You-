@echo off
REM Build the DNS resolver on Windows. Built by clavexis - github.com/clavexis
REM Windows needs Winsock; build under WSL with the linux/ Makefile, or adapt with -lws2_32.
where gcc >nul 2>nul && ( gcc -O2 -o dns.exe "%~dp0dns.c" -lws2_32 && echo Built dns.exe & goto :eof )
echo Build under WSL (recommended): cd linux ^&^& make
