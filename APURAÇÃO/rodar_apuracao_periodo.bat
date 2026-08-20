@echo off
chcp 65001 >nul
setlocal

cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
  set "PYTHON_CMD=py -3"
) else (
  set "PYTHON_CMD=python"
)

echo.
echo APURACAO POR PERIODO - SOMENTE EXCEL
echo.
echo Antes de rodar, confira se os caminhos das planilhas foram ajustados
echo no arquivo apuracao_periodo.py.
echo.

%PYTHON_CMD% -c "import openpyxl" >nul 2>nul
if errorlevel 1 (
  echo Instalando dependencia openpyxl...
  %PYTHON_CMD% -m pip install openpyxl
  if errorlevel 1 (
    echo.
    echo Nao foi possivel instalar o openpyxl automaticamente.
    echo Rode manualmente: pip install openpyxl
    pause
    exit /b 1
  )
)

set /p "DATA_INICIAL=Informe a data inicial (DD/MM/AAAA): "
set /p "DATA_FINAL=Informe a data final (DD/MM/AAAA): "

echo.
%PYTHON_CMD% "%~dp0apuracao_periodo.py" --periodo "%DATA_INICIAL%" "%DATA_FINAL%"

echo.
echo Se finalizou sem erro, veja o Excel gerado na pasta:
echo %~dp0outputs
echo.
pause
