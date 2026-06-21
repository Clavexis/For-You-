@echo off
REM Build the HTTP server on Windows (MinGW g++ or MSVC cl).
REM Built by clavexis - github.com/clavexis
where g++ >nul 2>nul && ( g++ -O2 -std=c++17 -o server.exe "%~dp0server.cpp" -lws2_32 && echo Built server.exe. Run: server.exe --port 8080 --root ..\www & goto :eof )
where cl >nul 2>nul && ( cl /O2 /EHsc /std:c++17 "%~dp0server.cpp" /Fe:server.exe ws2_32.lib && goto :eof )
echo No C++ compiler found. Install MinGW-w64 or MSVC Build Tools.
