@echo off
echo Starting installation and app...

REM Get the script's directory (project root)
set PROJECT_ROOT=%~dp0

REM Activate virtual environment
call "%PROJECT_ROOT%.venv\Scripts\activate"
if %ERRORLEVEL% NEQ 0 (
    echo Failed to activate virtual environment. Ensure .venv exists in %PROJECT_ROOT%.
    pause
    exit /b %ERRORLEVEL%
)

REM Install Python dependencies
echo Installing Python dependencies...
pip install -r "%PROJECT_ROOT%/src/backend/requirements.txt"
if %ERRORLEVEL% NEQ 0 (
    echo Failed to install Python dependencies. Check requirements.txt.
    echo Continuing with app startup...
) else (
    echo Python dependencies installed successfully.
)

REM Install Node.js dependencies
echo Installing Node.js dependencies...
cd /d "%PROJECT_ROOT%src\frontend"
call npm install
if %ERRORLEVEL% NEQ 0 (
    echo Failed to install Node.js dependencies. Check src\frontend\package.json.
    echo Continuing with app startup...
) else (
    echo Node.js dependencies installed successfully.
)

REM Return to project root
cd /d "%PROJECT_ROOT%"

REM Start backend in one terminal
echo Starting backend...
start cmd /k "cd /d %PROJECT_ROOT%src\backend && %PROJECT_ROOT%.venv\Scripts\activate && uvicorn app:app --reload --port 8000"

REM Start frontend in another terminal
echo Starting frontend...
start cmd /k "cd /d %PROJECT_ROOT%src\frontend && npm run dev"

echo Both backend and frontend are running!
