@echo off
echo === Återställer Gem-session ===
cd /d D:\Gem_Local
if exist logs\ (
    echo Tar bort gamla loggar...
    rmdir /s /q logs
)
mkdir logs
echo Startar ny Gem-session...
start powershell -ExecutionPolicy Bypass -File "D:\Gem-Local\gem_start.ps1"
exit
