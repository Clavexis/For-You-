@echo off
REM Install AI Resume Builder on Windows. Built by clavexis - github.com/clavexis
python -m pip install -r "%~dp0requirements.txt"
echo Installed. Try:  python "%~dp0resume.py" --resume me.txt --job jd.txt
