@echo off
setlocal
set "WUSHENG_INTERACTIVE=1"
for %%A in (%*) do if /I "%%~A"=="-CheckOnly" set "WUSHENG_INTERACTIVE=0"
for %%A in (%*) do if /I "%%~A"=="-Smoke" set "WUSHENG_INTERACTIVE=0"
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\launch.ps1" %*
set "WUSHENG_EXIT_CODE=%ERRORLEVEL%"
if not "%WUSHENG_EXIT_CODE%"=="0" if "%WUSHENG_INTERACTIVE%"=="1" pause
endlocal & exit /b %WUSHENG_EXIT_CODE%
