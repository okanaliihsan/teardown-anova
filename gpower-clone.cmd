@echo off
rem Paket kurulmadan calisan ince sarmalayici.
setlocal
set "HERE=%~dp0"
if defined PYTHONPATH (set "PYTHONPATH=%HERE%src;%PYTHONPATH%") else (set "PYTHONPATH=%HERE%src")
if not defined PYTHON set "PYTHON=python"
"%PYTHON%" -m anova_clone.cli %*
exit /b %ERRORLEVEL%
