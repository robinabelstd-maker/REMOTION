@echo off
:: Salesdock Scraper — Windows Setup Script
:: Run this once before running any scraper script

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

:: Install Python packages (no browser drivers needed)
echo.
echo Installing Python packages...
pip install requests beautifulsoup4 lxml gspread google-auth openpyxl

echo.
echo ============================================
echo  Setup complete! No browser install needed.
echo.
echo To run the test (38 transactions):
echo   python test_scraper.py
echo   python export_test.py
echo.
echo To run the full scraper:
echo   python scraper.py
echo   python export_to_excel.py
echo ============================================
pause
