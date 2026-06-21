@echo off
REM Build the compression tool on Windows. Built by clavexis - github.com/clavexis
where g++ >nul 2>nul && ( g++ -O2 -std=c++17 -o huff.exe "%~dp0huffman.cpp" && echo Built huff.exe & goto :eof )
where cl >nul 2>nul && ( cl /O2 /EHsc /std:c++17 "%~dp0huffman.cpp" /Fe:huff.exe && goto :eof )
echo No C++ compiler found. Install MinGW-w64 or MSVC.
