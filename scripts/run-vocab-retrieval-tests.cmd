@echo off
REM Culture vocab RAG retrieval tests (synthetic text -> retrieved terms)
REM Requires: .env with OPENAI_API_KEY, Chroma index built via ingest.py --reset

cd /d "%~dp0.."
set PYTHON=C:\Python314\python.exe

echo.
echo === Culture vocab retrieval tests ===
echo.

%PYTHON% backend\tests\vocab_retrieval_cases.py %*
set EXITCODE=%ERRORLEVEL%

echo.
if %EXITCODE%==0 (
    echo Done. Open data\test-results\vocab-retrieval-report.md for full retrieval table.
) else (
    echo Finished with failures. See output above and data\test-results\vocab-retrieval-report.md
)
exit /b %EXITCODE%
