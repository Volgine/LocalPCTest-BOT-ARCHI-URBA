@echo off
set COMMENT=auto: push depuis script
set BRANCH=dev

echo [GIT] Ajout des fichiers...
git add .

echo [GIT] Commit avec message : %COMMENT%
git commit -m "%COMMENT%"

echo [GIT] Push vers la branche : %BRANCH%
git push origin %BRANCH%

pause
