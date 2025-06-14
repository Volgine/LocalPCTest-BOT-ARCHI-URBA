@echo off
setlocal ENABLEEXTENSIONS

:: =====================================
:: 🔧 INSTALL_ALL.BAT – SETUP COMPLET
:: =====================================

:: Aller dans le dossier backend
cd /d "%~dp0backend"

:: Créer le venv si absent
if not exist ".venv" (
    echo [INFO] Création du venv...
    python -m venv .venv
)

:: Activer le venv
call .venv\Scripts\activate

:: Upgrade pip
python -m pip install --upgrade pip >nul 2>&1

:: Vérification du fichier de dépendances
if not exist requirements.txt (
    echo [ERREUR] Aucun fichier requirements.txt trouvé dans backend/.
    echo [ABORT] Impossible d’installer sans dépendances définies.
    pause
    exit /b
)

:: Installer les dépendances depuis requirements.txt
echo [INFO] Installation des dépendances depuis requirements.txt...
pip install -r requirements.txt

:: Corriger torch GPU si cassé
python -c "import torch" >nul 2>&1
if errorlevel 1 (
    echo [FIX] torch GPU détecté → reinstallation CPU
    pip uninstall torch -y
    pip install torch==2.1.0+cpu -f https://download.pytorch.org/whl/torch_stable.html
)

:: Retour racine + build Docker
cd ..
echo [DOCKER] Build image Docker...
docker build -t bot-archi-backend .

echo.
echo [✅] INSTALLATION TERMINEE
pause