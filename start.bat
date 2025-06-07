@echo off
echo ========================================
echo   Assistant Urbanisme - Demarrage
echo ========================================
echo.

:: Vérifier si l'environnement existe
if not exist backend\venv (
    echo [ERREUR] L'environnement virtuel n'existe pas !
    echo Lancez d'abord 'install.bat'
    pause
    exit /b 1
)

:: Démarrer le backend dans une nouvelle fenêtre
echo Demarrage du backend (API)...
start "Backend - Urbanisme API" cmd /k "cd backend && venv\Scripts\activate && uvicorn main:app --reload"

:: Attendre un peu que le backend démarre
timeout /t 3 /nobreak >nul

:: Démarrer le frontend dans une nouvelle fenêtre
echo Demarrage du frontend (Interface)...
start "Frontend - Urbanisme" cmd /k "cd frontend && python -m http.server 3000"

:: Attendre un peu avant d'ouvrir le navigateur
timeout /t 2 /nobreak >nul

:: Ouvrir le navigateur
echo.
echo Ouverture du navigateur...
start http://localhost:3000

echo.
echo ========================================
echo   Application lancee !
echo ========================================
echo.
echo Backend  : http://localhost:8000
echo Frontend : http://localhost:3000
echo API Docs : http://localhost:8000/docs
echo.
echo Pour arreter : Fermez les fenetres Backend et Frontend
echo.
pause