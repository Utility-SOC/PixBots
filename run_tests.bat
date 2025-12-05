@echo off
echo Running Tests...
.\Scripts\python.exe -m pytest
if %ERRORLEVEL% EQU 0 (
    echo Tests Passed!
) else (
    echo Tests Failed!
)
pause
