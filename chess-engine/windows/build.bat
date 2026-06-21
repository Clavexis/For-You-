@echo off
REM Build the chess engine on Windows. Built by clavexis - github.com/clavexis
REM Requires either MinGW (g++) or MSVC (cl) on your PATH.
where g++ >nul 2>nul
if %errorlevel%==0 (
  g++ -O2 -std=c++17 -o chess.exe "%~dp0chess.cpp"
  echo Built chess.exe with g++. Run it with:  chess.exe
  goto :eof
)
where cl >nul 2>nul
if %errorlevel%==0 (
  cl /O2 /EHsc /std:c++17 "%~dp0chess.cpp" /Fe:chess.exe
  echo Built chess.exe with MSVC. Run it with:  chess.exe
  goto :eof
)
echo No C++ compiler found. Install MinGW-w64 (g++) or Visual Studio Build Tools (cl).
exit /b 1
