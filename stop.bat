@echo off
echo ========================================
echo   Arret de l'application
echo ========================================
echo.

:: Tuer les processus Python (uvicorn et http.server)
echo Arret des serveurs...
taskkill /F /IM python.exe /T >nul 2>&1

echo [OK] Application arretee
echo.
pause