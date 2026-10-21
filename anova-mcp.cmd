@echo off
rem MCP sunucusu (stdio) icin paket kurulmadan calisan ince sarmalayici.
setlocal
set "HERE=%~dp0"
if defined PYTHONPATH (set "PYTHONPATH=%HERE%src;%PYTHONPATH%") else (set "PYTHONPATH=%HERE%src")
if not defined PYTHON set "PYTHON=python"
"%PYTHON%" -m anova_clone.mcp_server %*
exit /b %ERRORLEVEL%
