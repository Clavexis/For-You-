@echo off
REM Build the AES tool on Windows. Built by clavexis - github.com/clavexis
where g++ >nul 2>nul && ( g++ -O2 -std=c++17 -o aes.exe "%~dp0aes.cpp" && echo Built aes.exe. Verify: aes.exe --test & goto :eof )
where cl >nul 2>nul && ( cl /O2 /EHsc /std:c++17 "%~dp0aes.cpp" /Fe:aes.exe && goto :eof )
echo No C++ compiler found. Install MinGW-w64 or MSVC.
