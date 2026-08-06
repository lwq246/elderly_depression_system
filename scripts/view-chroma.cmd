@echo off
REM View Chroma RAG data from Command Prompt.
REM Usage:
REM   view-chroma
REM   view-chroma --type culture_vocabulary --locale en-SG
REM   view-chroma --term sian --full
REM   view-chroma --json

setlocal
set "ROOT=%~dp0.."
set "PYTHON=C:\Python314\python.exe"
"%PYTHON%" "%ROOT%\backend\rag\inspect_index.py" %*
