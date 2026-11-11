@echo off
rem Starts ShipGame from any terminal. Clearing ELECTRON_RUN_AS_NODE matters inside tools that set
rem it (it makes the app quit straight away).
set ELECTRON_RUN_AS_NODE=
start "" "%LOCALAPPDATA%\ShipGame\build\dist\ShipGame-win32-x64\ShipGame.exe"
