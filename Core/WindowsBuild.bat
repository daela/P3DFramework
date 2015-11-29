@echo off
mkdir Windows
cd Windows
cmake ../ -G"Visual Studio 10 Win64"
REM vcexpress.exe RSCoreModules.sln /build Release
pause