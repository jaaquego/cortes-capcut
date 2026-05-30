@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Vigia de Exportacao CapCut
echo ============================================
echo   Exportador CapCut - Vigia de pasta
echo ============================================
echo.
echo Exporte a timeline INTEIRA do CapCut na pasta vigiada.
echo Os 15 cortes saem organizados sozinhos. Feche esta janela para parar.
echo.
py "%~dp0vigiar.py"
echo.
echo (Vigia encerrado.)
pause
