@echo off
cd %HYBRIS_DIR%\bin\platform
call setantenv.bat 
call ant all
IF %errorlevel%==0 (
    echo Ant all success, running server
    hybrisserver.bat debug
) ELSE (
    echo Ant all failure: %errorlevel%
    PAUSE
)