@echo off
REM Install AI Dungeon on Windows. Built by clavexis - github.com/clavexis
python -m pip install -r "%~dp0requirements.txt"
echo Installed. Play with:  python "%~dp0dungeon.py"
echo (Set ANTHROPIC_API_KEY for AI-generated narration.)
