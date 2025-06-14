@echo off
setlocal ENABLEEXTENSIONS

for /f "tokens=*" %%i in ('git rev-parse --abbrev-ref HEAD') do set BRANCH=%%i

set /p COMMENT=[GIT] Message du commit : 

echo [GIT] Ajout des fichiers...
git add .

:: Vérifie s’il y a quelque chose à commit
for /f %%C in ('git diff --cached --name-only') do set HASCHANGES=1
if not defined HASCHANGES (
    echo [GIT] Rien à commit. Arret.
    pause
    exit /b
)

echo [GIT] Commit sur la branche %BRANCH% avec message : %COMMENT%
git commit -m "%COMMENT%"

echo [GIT] Pull + rebase avant push...
git pull origin %BRANCH% --rebase

echo [GIT] Push vers la branche : %BRANCH%
git push origin %BRANCH%

pause
