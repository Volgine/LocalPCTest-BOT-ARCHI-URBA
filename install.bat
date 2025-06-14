@echo off
echo ========================================
echo   🚀 DEPLOYMENT RAILWAY - URBA.AI
echo ========================================
echo.

:: Vérifier si Railway CLI est installé
railway --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Railway CLI non installé !
    echo Installez-le : npm install -g @railway/cli
    pause
    exit /b 1
)

:: Vérifier si on est connecté
railway whoami >nul 2>&1
if errorlevel 1 (
    echo [AUTH] Connexion à Railway...
    railway login
)

echo [CHECK] Vérification de la structure...

:: Vérifier les fichiers critiques
if not exist "backend\main.py" (
    echo [ERREUR] backend/main.py manquant !
    pause
    exit /b 1
)

if not exist "backend\requirements.txt" (
    echo [ERREUR] backend/requirements.txt manquant !
    pause
    exit /b 1
)

:: Supprimer l'ancien Dockerfile problématique s'il existe
if exist "Dockerfile" (
    echo [FIX] Suppression du Dockerfile racine problématique...
    del Dockerfile
)

:: Créer railway.toml optimisé
echo [CONFIG] Création du railway.toml optimisé...
echo [build] > railway.toml
echo builder = "NIXPACKS" >> railway.toml
echo buildCommand = "cd backend && pip install -r requirements.txt && python -c 'from sentence_transformers import SentenceTransformer; SentenceTransformer(\"all-MiniLM-L6-v2\")'" >> railway.toml
echo. >> railway.toml
echo [deploy] >> railway.toml
echo startCommand = "cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT" >> railway.toml
echo restartPolicyType = "ON_FAILURE" >> railway.toml
echo restartPolicyMaxRetries = 10 >> railway.toml
echo healthcheckPath = "/health" >> railway.toml
echo healthcheckTimeout = 60 >> railway.toml

:: Vérifier les variables d'environnement
echo.
echo [ENV] Variables d'environnement à configurer :
echo - GROQ_API_KEY=gsk_votre_cle_ici
echo.
set /p CONTINUE=Continuer le déploiement ? (y/N) : 
if /i not "%CONTINUE%"=="y" (
    echo Déploiement annulé.
    pause
    exit /b 0
)

:: Commit les changements si nécessaire
echo [GIT] Vérification des changements...
git status --porcelain >nul 2>&1
if not errorlevel 1 (
    for /f %%i in ('git status --porcelain') do (
        echo [GIT] Commit des changements...
        git add .
        git commit -m "Fix Railway deployment configuration"
        goto :deploy
    )
)

:deploy
echo [DEPLOY] Déploiement en cours...
railway up

if errorlevel 1 (
    echo.
    echo [ERREUR] Déploiement échoué !
    echo.
    echo Solutions à essayer :
    echo 1. Vérifier GROQ_API_KEY dans Railway dashboard
    echo 2. Regarder les logs : railway logs
    echo 3. Tester localement : railway run python backend/main.py
    echo.
) else (
    echo.
    echo [SUCCESS] ✅ Déploiement réussi !
    echo.
    echo Commandes utiles :
    echo - railway logs --follow : voir les logs
    echo - railway open : ouvrir l'app
    echo - railway status : statut du service
    echo.
)

pause
