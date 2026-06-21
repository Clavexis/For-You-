@echo off
REM Multiplayer Game on Windows. Built by clavexis - github.com/clavexis
REM
REM The server/client use BSD sockets; the simplest Windows path is WSL (Ubuntu):
REM   sudo apt install build-essential libsdl2-dev
REM   cd /mnt/c/path/to/multiplayer-game-cpp/linux && make
REM
REM Or with MinGW + SDL2 (server needs -lws2_32 with a Winsock adaptation).
echo See README: build under WSL with the linux/ Makefile, or use MinGW + SDL2.
