@echo off
setlocal
title Numerical study
cd /d "%~dp0.."

if not exist "src\shapdp.py" goto not_extracted

rem Everything goes inside this folder. Deleting the folder removes all of it.
set "STUDY_ENV=%CD%\.study_environment"
set "UV_VERSION=0.13.6"
set "PYTHON_VERSION=3.14.7"
set "UV_CACHE_DIR=%STUDY_ENV%\cache"
set "UV_PYTHON_INSTALL_DIR=%STUDY_ENV%\python"
set "UV_PYTHON_BIN_DIR=%STUDY_ENV%\bin"
set "UV_PYTHON_PREFERENCE=only-managed"
set "UV_NO_CONFIG=1"
set "JUPYTER_CONFIG_DIR=%STUDY_ENV%\jupyter\config"
set "JUPYTER_DATA_DIR=%STUDY_ENV%\jupyter\data"
set "JUPYTER_RUNTIME_DIR=%STUDY_ENV%\jupyter\runtime"
set "IPYTHONDIR=%STUDY_ENV%\ipython"
set "MPLCONFIGDIR=%STUDY_ENV%\matplotlib"

rem The private Python only works in the folder where it was set up, so moving this folder repeats the setup.
set "READY_FOLDER="
if exist "%STUDY_ENV%\ready.txt" set /p READY_FOLDER=<"%STUDY_ENV%\ready.txt"
if /i "%READY_FOLDER%"=="%CD%" goto open_notebook
if exist "%STUDY_ENV%" rmdir /s /q "%STUDY_ENV%"

echo.
echo  First time only: setting up a private copy of Python and the study's packages.
echo  It needs an internet connection and installs nothing outside this folder.
echo.
if not exist "%STUDY_ENV%" mkdir "%STUDY_ENV%"

echo  [1 of 4] Downloading the installer...
"%SystemRoot%\System32\curl.exe" -fsSL -o "%STUDY_ENV%\uv.zip" "https://github.com/astral-sh/uv/releases/download/%UV_VERSION%/uv-x86_64-pc-windows-msvc.zip"
if errorlevel 1 goto failed
"%SystemRoot%\System32\tar.exe" -xf "%STUDY_ENV%\uv.zip" -C "%STUDY_ENV%"
if errorlevel 1 goto failed

echo  [2 of 4] Getting Python %PYTHON_VERSION%...
"%STUDY_ENV%\uv.exe" python install %PYTHON_VERSION% --no-registry
if errorlevel 1 goto failed

echo  [3 of 4] Creating the environment...
"%STUDY_ENV%\uv.exe" venv --python %PYTHON_VERSION% "%STUDY_ENV%\venv"
if errorlevel 1 goto failed

echo  [4 of 4] Installing the exact package versions...
"%STUDY_ENV%\uv.exe" pip sync --python "%STUDY_ENV%\venv\Scripts\python.exe" --require-hashes requirements-notebook.lock
if errorlevel 1 goto failed

rem Register the private kernel, so that Jupyter does not pick up another Python on this computer.
"%STUDY_ENV%\venv\Scripts\python.exe" -m ipykernel install --user --name python3 --display-name "Python 3"
if errorlevel 1 goto failed

> "%STUDY_ENV%\ready.txt" cd

:open_notebook
if /i "%~1"=="--check" goto check

echo.
echo  Opening the notebook in your browser.
echo  Keep this window open while you use it. Close it when you finish.
echo.
"%STUDY_ENV%\venv\Scripts\python.exe" -m notebook "notebook\reproduce_results.ipynb"
goto end

:check
"%STUDY_ENV%\venv\Scripts\python.exe" -m nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=1800 "notebook\reproduce_results.ipynb"
if errorlevel 1 goto failed
"%STUDY_ENV%\venv\Scripts\python.exe" -m nbconvert --to html "notebook\reproduce_results.ipynb"
if errorlevel 1 goto failed
echo CHECK PASSED
exit /b 0

:not_extracted
echo.
echo  Please extract the whole zip file to a folder first, then run this file from there.
echo.
pause
exit /b 1

:failed
echo.
echo  Something went wrong. Check the internet connection and run this file again.
echo  If it still fails, delete the folder .study_environment here and try once more.
echo  You can read all the results without installing anything: open
echo  notebook\reproduce_results.html in a browser.
echo.
if /i not "%~1"=="--check" pause
exit /b 1

:end
endlocal
