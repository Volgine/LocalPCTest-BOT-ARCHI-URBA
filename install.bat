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

:: Lancer l'API localement avec uvicorn
echo [API] Lancement local sur http://localhost:8000 ...
uvicorn main:app --host 0.0.0.0 --port 8000

:: =====================================
:: 🚀 DEPLOY_RAILWAY.BAT – DEPLOIEMENT
:: =====================================

:deploy_railway
@echo off
echo [RAILWAY] Déploiement en cours...
railway up
pause

:: =====================================
:: 📥 COMMIT_LOCAL.BAT – COMMIT SEUL
:: =====================================

:commit_local
@echo off
setlocal ENABLEEXTENSIONS

for /f "tokens=*" %%i in ('git rev-parse --abbrev-ref HEAD') do set BRANCH=%%i

set /p COMMENT=[GIT] Message du commit : 

echo [GIT] Ajout des fichiers...
git add .

echo [GIT] Commit sur la branche %BRANCH% avec message : %COMMENT%
git commit -m "%COMMENT%"

echo.
echo [✅] Commit local OK – rien n’a été pushé.
pause
