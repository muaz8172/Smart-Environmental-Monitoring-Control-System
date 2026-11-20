"""
Name   : Muhammad Muaz Bin Md Fazli
Uni    : UniKL MFI
Topic  : Smart Environmental & Monitoring System
Lists COM ports and marks the one that looks like the Arduino.
Usage  : python find_port.py
"""

from serial.tools import list_ports

ARDUINO_VIDS = {0x2341: "Arduino", 0x2A03: "Arduino", 0x1A86: "CH340 clone", 0x0403: "FTDI"}

ports = list_ports.comports()
if not ports:
    print("No COM ports found. Plug in the Arduino USB cable.")
for p in ports:
    tag = f"  <- {ARDUINO_VIDS[p.vid]} (use this)" if p.vid in ARDUINO_VIDS else ""
    print(f"{p.device:7} {p.description}{tag}")
