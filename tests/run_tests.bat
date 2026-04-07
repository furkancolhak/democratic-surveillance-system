@echo off
REM Test Runner Script for Windows
REM Runs all test suites with proper error handling

setlocal enabledelayedexpansion

echo ======================================================================
echo   🔬 SURVEILLANCE SYSTEM - TEST SUITE
echo ======================================================================
echo.

REM Check if we're in the right directory
if not exist "tests" (
    echo ❌ Error: Must run from project root directory
    exit /b 1
)

REM Track results
set TOTAL=0
set PASSED=0
set FAILED=0

REM Quick smoke test
echo.
echo ======================================================================
echo   Running: Quick Smoke Test
echo ======================================================================
python tests\quick_test.py
if %ERRORLEVEL% EQU 0 (
    echo ✅ Quick Smoke Test PASSED
    set /a PASSED+=1
) else (
    echo ❌ Quick Smoke Test FAILED
    set /a FAILED+=1
)
set /a TOTAL+=1

REM Comprehensive unit tests
echo.
echo ======================================================================
echo   Running: Comprehensive Unit Tests
echo ======================================================================
python tests\test_comprehensive.py
if %ERRORLEVEL% EQU 0 (
    echo ✅ Comprehensive Unit Tests PASSED
    set /a PASSED+=1
) else (
    echo ❌ Comprehensive Unit Tests FAILED
    set /a FAILED+=1
)
set /a TOTAL+=1

REM Database tests (optional)
echo.
echo ======================================================================
echo   Checking database availability...
echo ======================================================================

python -c "import sys; sys.path.append('app/core'); from database import db_manager; session = db_manager.get_session(); session.execute('SELECT 1'); session.close()" 2>nul
if %ERRORLEVEL% EQU 0 (
    echo ✅ Database available
    
    echo.
    echo ======================================================================
    echo   Running: Database Integration Tests
    echo ======================================================================
    python tests\test_with_database.py
    if !ERRORLEVEL! EQU 0 (
        echo ✅ Database Integration Tests PASSED
        set /a PASSED+=1
    ) else (
        echo ❌ Database Integration Tests FAILED
        set /a FAILED+=1
    )
    set /a TOTAL+=1
) else (
    echo ⚠️  Database not available - skipping integration tests
    echo    To run database tests:
    echo    cd docker ^&^& docker-compose up -d postgres
)

REM Final summary
echo.
echo ======================================================================
echo   📊 FINAL SUMMARY
echo ======================================================================
echo Total Tests: %TOTAL%
echo Passed: %PASSED%
echo Failed: %FAILED%
echo.

if %FAILED% EQU 0 (
    echo 🎉 ALL TESTS PASSED!
    echo ✅ System is ready
    exit /b 0
) else (
    echo ⚠️  SOME TESTS FAILED
    echo ❌ Please review failures
    exit /b 1
)
