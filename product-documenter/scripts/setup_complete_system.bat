@echo off
echo ========================================
echo 🚀 PRODUCT DOCUMENTER AI - COMPLETE SETUP
echo ========================================
echo.

echo [1] Checking Python and pip...
python --version
pip --version

echo.
echo [2] Installing required packages...
pip install openai flask python-dotenv streamlit pandas sqlite3 requests

echo.
echo [3] Setting up database...
python setup_database.py

echo.
echo [4] Checking OpenAI API key...
if not exist .env (
    echo Creating .env file...
    echo OPENAI_API_KEY=your_key_here > .env
    echo OPENAI_MODEL=gpt-3.5-turbo >> .env
    echo MONTHLY_BUDGET=50 >> .env
    echo.
    echo ⚠️  Please edit .env file and add your real OpenAI API key
    echo     Get one from: https://platform.openai.com/api-keys
    pause
)

echo.
echo [5] Testing OpenAI connection...
python document_generator.py

echo.
echo ========================================
echo ✅ SETUP COMPLETE!
echo ========================================
echo.
echo Next steps to run the system:
echo.
echo 1. Start API Server (Terminal 1):
echo    python api_server.py
echo.
echo 2. Start Dashboard (Terminal 2):
echo    streamlit run monitor_dashboard.py
echo.
echo 3. Generate Documents (Terminal 3):
echo    Use the test commands below
echo.
pause