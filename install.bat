@echo off
echo ========================================
echo   Assistant Urbanisme - Installation
echo ========================================
echo.

:: Vérifier si Python est installé
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python n'est pas installe !
    echo Telecharge Python depuis : https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [OK] Python est installe
echo.

:: Créer l'environnement virtuel
echo Creation de l'environnement virtuel...
cd backend
if exist venv (
    echo [INFO] L'environnement virtuel existe deja
) else (
    python -m venv venv
    echo [OK] Environnement virtuel cree
)

:: Activer l'environnement et installer les dépendances
echo.
echo Installation des dependances Python...
call venv\Scripts\activate.bat
pip install -r requirements.txt
echo [OK] Dependances installees

:: Créer le fichier .env s'il n'existe pas
if not exist .env (
    echo.
    echo Creation du fichier .env...
    copy .env.example .env
    echo [OK] Fichier .env cree - Pensez a ajouter vos cles API !
)

:: Retour au dossier principal
cd ..

echo.
echo ========================================
echo   Installation terminee !
echo ========================================
echo.
echo Pour lancer l'application :
echo 1. Double-cliquez sur 'start.bat'
echo.
echo Ou manuellement :
echo - Backend : cd backend puis uvicorn main:app --reload
echo - Frontend : cd frontend puis python -m http.server 3000
echo.
pause