@echo off
REM Build clawpkg on Windows. Built by clavexis - github.com/clavexis
cargo build --release
echo Built target\release\clawpkg.exe - try: target\release\clawpkg.exe install leftpad
