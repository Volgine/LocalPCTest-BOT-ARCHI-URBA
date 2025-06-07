@echo off
echo ========================================
echo   Tests de performance
echo ========================================
echo.

:: Vérifier si l'environnement existe
if not exist backend\venv (
    echo [ERREUR] L'environnement virtuel n'existe pas !
    echo Lancez d'abord 'install.bat'
    pause
    exit /b 1
)

:: Vérifier si le backend est lancé
curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Le backend n'est pas lance !
    echo Lancez d'abord 'start.bat'
    pause
    exit /b 1
)

:: Lancer les tests
echo Lancement des tests...
echo.
cd tests
..\backend\venv\Scripts\python.exe test_load.py
cd ..

echo.
pause