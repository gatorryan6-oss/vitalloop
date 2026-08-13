@echo off
REM run.bat — one double-click to launch Vital Loop. No commands to remember.
REM Claude Code: keep this file working at every milestone. If launching
REM changes, this file changes with it.

cd /d "%~dp0"

REM This project's dedicated port. MUST match PORT in verify.py
REM (guarded by tests/test_invariants.py).
set PORT=5083

REM Activate the virtual environment if there is one.
if exist ".venv\Scripts\activate.bat" call ".venv\Scripts\activate.bat"
if exist "venv\Scripts\activate.bat" call "venv\Scripts\activate.bat"

REM Until M2 there is no web app to launch — say so plainly instead of erroring.
if not exist "app.py" (
    echo Vital Loop's web app isn't built yet — that lands at milestone M2.
    echo For now you can run:  python -m engine.demo   ^(after M1^)
    echo and:  python verify.py   and   python -m pytest -q
    echo.
    pause
    exit /b 0
)

echo Starting Vital Loop... when you see it's running, open http://127.0.0.1:%PORT%/
start "" http://127.0.0.1:%PORT%/
REM ---- EDIT THIS ONE LINE PER PROJECT ----
python app.py
REM -----------------------------------------

REM Keep the window open if the app crashes, so the error is readable.
echo.
echo Vital Loop has stopped. If there is an error above, screenshot or copy it.
pause
