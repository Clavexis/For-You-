@echo off
REM Install Voice to Code on Windows. Built by clavexis - github.com/clavexis
setlocal
python -m pip install anthropic
echo ^>^> (Optional) for mic + offline transcription:
echo    pip install sounddevice numpy openai-whisper
echo ^>^> Installed. Try:
echo    python "%~dp0voice_to_code.py" --text "a CLI calculator" --lang python
endlocal
