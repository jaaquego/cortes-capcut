@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================================
echo  EXPORTADOR AUTOMATICO CAPCUT
echo  Deixe aberto SO o projeto que quer exportar (feche os outros).
echo  O programa faz o resto: exporta, corta, organiza e sobe.
echo ============================================================
echo.
py -u exportar_auto.py
echo.
echo ============================================================
pause
