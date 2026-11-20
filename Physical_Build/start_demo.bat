@echo off
REM Muhammad Muaz Bin Md Fazli, UniKL MFI - Smart Environmental & Monitoring System
REM Starts the serial bridge + AI brain and opens the dashboard. Mosquitto and Node-RED must already be running.
REM Usage: start_demo.bat COM3   (or double-click and type the port)

set PORT=%1
if "%PORT%"=="" (
    py "%~dp0python\find_port.py"
    set /p PORT=Arduino COM port, e.g. COM3:
)

start "Serial-MQTT bridge" cmd /k py "%~dp0python\serial_mqtt_bridge.py" --port %PORT%
timeout /t 3 >nul
start "AI brain" cmd /k py "%~dp0python\ai_brain.py"
timeout /t 2 >nul
start "" http://localhost:1880/ir7
