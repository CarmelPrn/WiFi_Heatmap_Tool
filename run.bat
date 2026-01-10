@echo on
setlocal

echo Launching WiFi Heatmap Tool

echo Checking If Python is installed...
where python
if errorlevel 1 (
    echo Cannot find Python. Please install Python 3.11+
    pause
    exit /b 1
)

python --version

python -m pip install --upgrade pip

python -m pip show uv
if errorlevel 1 (
	echo Installing uv...
	python -m pip install uv
	if errorlevel 1 (
		echo Failed to install uv
		pause
		exit /b
	)
)

echo Using pyproject.toml to sync environment
python -m uv sync
if errorlevel 1 (
	echo uv sync failed
	pause
	exit /b
)


echo Starting application...
python -m uv run python main.py


endlocal
