@echo off
REM Build Claw on Windows (MinGW g++ or MSVC cl). Built by clavexis - github.com/clavexis
where g++ >nul 2>nul && ( g++ -O2 -std=c++17 -o claw.exe "%~dp0claw.cpp" && echo Built claw.exe. Try: claw.exe ..\examples\fib.claw & goto :eof )
where cl >nul 2>nul && ( cl /O2 /EHsc /std:c++17 "%~dp0claw.cpp" /Fe:claw.exe && goto :eof )
echo No C++ compiler found. Install MinGW-w64 or MSVC Build Tools.
