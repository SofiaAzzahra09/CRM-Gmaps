@echo off
chcp 65001 >nul
title Push CRM-Gmaps ke GitHub

echo ============================================================
echo   MENGUNGGAH PROYEK KE GITHUB (CRM-Gmaps)
echo ============================================================
echo.
echo Melakukan push ke origin main...
echo.

git push -u origin main

echo.
echo ============================================================
echo   Selesai! Cek repositori: https://github.com/SofiaAzzahra09/CRM-Gmaps
echo ============================================================
echo.
pause
