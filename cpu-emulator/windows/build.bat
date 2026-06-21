@echo off
REM Build the CHIP-8 emulator on Windows. Built by clavexis - github.com/clavexis
where g++ >nul 2>nul && ( g++ -O2 -std=c++17 -o chip8.exe "%~dp0chip8.cpp" "%~dp0main.cpp" && echo Built chip8.exe. Verify: chip8.exe --test & goto :eof )
where cl >nul 2>nul && ( cl /O2 /EHsc /std:c++17 "%~dp0chip8.cpp" "%~dp0main.cpp" /Fe:chip8.exe && goto :eof )
echo No C++ compiler found. Install MinGW-w64 or MSVC.
