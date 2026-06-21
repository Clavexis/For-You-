@echo off
REM Build the ray tracer on Windows (MinGW g++ or MSVC cl). Built by clavexis - github.com/clavexis
where g++ >nul 2>nul && ( g++ -O2 -std=c++17 -o raytracer.exe "%~dp0raytracer.cpp" && echo Built raytracer.exe. Try: raytracer.exe -o render.png --samples 3 & goto :eof )
where cl >nul 2>nul && ( cl /O2 /EHsc /std:c++17 "%~dp0raytracer.cpp" /Fe:raytracer.exe && goto :eof )
echo No C++ compiler found. Install MinGW-w64 or MSVC Build Tools.
