@echo off
chcp 65001 >nul
title Instalar - Cortes CapCut
color 0B
cd /d "%~dp0"
cls
echo.
echo   ============================================================
echo                 INSTALADOR - Cortes CapCut
echo   ============================================================
echo.

REM ---- 1) Python ----
where py >nul 2>nul
if %errorlevel%==0 goto temPython
echo   Python nao encontrado. Vou instalar (via winget)...
echo.
winget install -e --id Python.Python.3.12 --silent --accept-source-agreements --accept-package-agreements
echo.
echo   ------------------------------------------------------------
echo   Python instalado. FECHE esta janela e rode o "Instalar.bat"
echo   MAIS UMA VEZ para concluir a instalacao.
echo   ------------------------------------------------------------
echo.
pause
exit /b

:temPython
echo   [1/3] Python encontrado.
echo   [2/3] Instalando as bibliotecas (pode levar alguns minutos)...
py -m pip install --upgrade pip >nul 2>nul
py -m pip install -r requirements.txt
if errorlevel 1 (
  echo.
  echo   ERRO ao instalar as bibliotecas. Verifique sua internet e tente de novo.
  pause
  exit /b
)
echo   [3/3] Criando o atalho na Area de Trabalho...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0criar_atalho.ps1"
echo.
echo   ============================================================
echo   PRONTO! Procure o atalho "Cortes CapCut" na Area de Trabalho.
echo.
echo   Antes de usar, confira:
echo     - CapCut Desktop instalado
echo     - Google Drive para Desktop instalado (se for salvar no Drive)
echo   Na 1a vez, o programa pergunta a pasta de destino dos cortes.
echo   ============================================================
echo.
pause
