@REM ----------------------------------------------------------------------------
@REM Maven Wrapper Script for Windows
@REM ----------------------------------------------------------------------------
@echo off
setlocal

if not defined JAVA_HOME (
    if exist "C:\Program Files\Microsoft\jdk-21.0.13.21-hotspot" (
        set "JAVA_HOME=C:\Program Files\Microsoft\jdk-21.0.13.21-hotspot"
    )
)

if defined JAVA_HOME (
    set "PATH=%JAVA_HOME%\bin;%PATH%"
)

if exist "C:\Users\DELL\apache-maven-3.9.9\bin\mvn.cmd" (
    call "C:\Users\DELL\apache-maven-3.9.9\bin\mvn.cmd" %*
) else (
    call mvn %*
)
