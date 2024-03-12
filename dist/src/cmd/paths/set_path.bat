@echo off

@REM do not run this code many times.
for %%I in ("%~dp0..\..\..\..") do set "FluxarPath=%%~fI"
setx PATH "%FluxarPath%;%PATH%" /m >NUL
