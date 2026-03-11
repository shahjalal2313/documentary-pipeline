@echo off
REM Batch Runner for Documentary Production
REM Usage: run_production.bat <script_json> <batch_size> <start_id>
REM Example: run_production.bat output/scripts/the_rise_and_fall_of_wework.json 3 1

set SCRIPT=%1
set BATCH_SIZE=%2
set START_ID=%3

if "%SCRIPT%"=="" (
    echo Error: Missing script path.
    echo Usage: run_production.bat ^<script_json^> [batch_size] [start_id]
    exit /b 1
)

if "%BATCH_SIZE%"=="" set BATCH_SIZE=3
if "%START_ID%"=="" set START_ID=1

echo --- STARTING BATCH PRODUCTION ---
echo Script: %SCRIPT%
echo Batch Size: %BATCH_SIZE%
echo Starting ID: %START_ID%
echo ---------------------------------

venv\Scripts\python.exe batch_producer.py %SCRIPT% %BATCH_SIZE% %START_ID%

pause
