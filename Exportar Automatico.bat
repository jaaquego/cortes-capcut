@echo off
chcp 65001 >nul
title Exportar Cortes CapCut
color 0B
cd /d "%~dp0"
cls
echo.
echo   ============================================================
echo.
echo               EXPORTADOR DE CORTES  --  CapCut
echo.
echo   ============================================================
echo.
echo     Antes de comecar:
echo       1. Deixe aberto SO o projeto que quer exportar
echo       2. Nao mexa no mouse durante os segundos de clique
echo.
echo     O programa faz sozinho:
echo       exporta  --  corta  --  organiza no Drive  --  abre a pasta
echo.
echo   ------------------------------------------------------------
echo.
py -u exportar_auto.py
echo.
echo   ------------------------------------------------------------
echo     Concluido. Pode fechar esta janela.
echo.
pause >nul
