@echo off
chcp 65001 >nul
title Google Maps Global Lead Scraper (Target Klien Website)

set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
if not exist "%PYTHON_EXE%" (
    set "PYTHON_EXE=python"
)

echo ============================================================
echo   GOOGLE MAPS LEAD SCRAPER - TARGET KLIEN WEBSITE (GLOBAL)
echo ============================================================
echo.
echo Contoh Pencarian Internasional:
echo   - restaurants, bakeries, cafes in London
echo   - plumbers, electricians, roofers in Miami
echo   - hair salons, barbershops in Sydney
echo   - dentists, clinics in Singapore
echo   - restaurants, coffee shops in Dubai
echo.
echo Contoh Pencarian Domestik:
echo   - restoran, rumah makan, umkm, cake shop di Cianjur
echo   - cafe, resto di Bandung
echo.
echo ============================================================
set /p QUERY="Masukkan kata kunci pencarian: "
if "%QUERY%"=="" set "QUERY=restaurants, cafes in London"

set /p LIMIT="Masukkan target data per kategori (default 20): "
if "%LIMIT%"=="" set "LIMIT=20"

echo.
echo [INFO] Menjalankan scraper untuk: "%QUERY%" (Target %LIMIT% per kategori)...
echo Browser akan terbuka secara otomatis untuk mengambil data.
echo.

"%PYTHON_EXE%" scraper.py --query "%QUERY%" --limit %LIMIT%

echo.
echo ============================================================
echo   Proses Selesai! File Excel tersimpan di folder 'hasil_scraping'.
echo ============================================================
echo.
pause
