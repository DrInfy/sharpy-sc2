@echo off

REM create virtual environment
python -m venv .venv

REM activate virtual environment, install requirements, and upgrade pip
REM these need to be chained or otherwise "pip install" commands will not run after the activate command
.venv\Scripts\activate.bat & pip install -r requirements.txt & pip install -r requirements.dev.txt & python -m pip install --upgrade pip
