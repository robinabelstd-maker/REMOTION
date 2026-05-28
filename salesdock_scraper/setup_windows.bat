@echo off
:: Salesdock Scraper — Windows Setup Script
:: Run this once before running scraper.py

echo ============================================
echo  Salesdock Scraper Setup
echo ============================================

:: Create output folder on Desktop
set EXPORT_DIR=%USERPROFILE%\Desktop\salesdock_export
if not exist "%EXPORT_DIR%" (
    mkdir "%EXPORT_DIR%"
    echo Created folder: %EXPORT_DIR%
) else (
    echo Folder already exists: %EXPORT_DIR%
)

:: Install Python packages
echo.
echo Installing Python packages...
pip install playwright gspread google-auth openpyxl

:: Install Playwright browsers (Chromium not needed — we use system Chrome)
:: But we still need Playwright's browser bindings
echo.
echo Installing Playwright Chrome driver...
playwright install chrome

echo.
echo ============================================
echo  Setup complete!
echo.
echo IMPORTANT: Before running the scraper,
echo make sure Chrome is CLOSED completely.
echo Playwright needs exclusive access to the
echo Chrome profile.
echo.
echo Then run:
echo   python scraper.py
echo ============================================
pause
