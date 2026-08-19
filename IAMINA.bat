@echo off
setlocal
cd /d "%~dp0" || exit /b 1
python "%~dp0IAMINA.py" %*
set "IAMINA_EXIT=%ERRORLEVEL%"
if not "%IAMINA_EXIT%"=="0" if "%CI%"=="" pause
exit /b %IAMINA_EXIT%
