@echo off
REM Build the neural network on Windows. Built by clavexis - github.com/clavexis
where g++ >nul 2>nul && ( g++ -O3 -std=c++17 -o neuralnet.exe "%~dp0neuralnet.cpp" && echo Built neuralnet.exe. Try: neuralnet.exe --demo & goto :eof )
where cl >nul 2>nul && ( cl /O2 /EHsc /std:c++17 "%~dp0neuralnet.cpp" /Fe:neuralnet.exe && goto :eof )
echo No C++ compiler found. Install MinGW-w64 or MSVC Build Tools.
