"""
Name   : Muhammad Muaz Bin Md Fazli
Uni    : UniKL MFI
Topic  : Smart Environmental & Monitoring System
Checks the PC -> Arduino direction on COM2 (Proteus COMPIM RXD -> Arduino RX).
Run with Proteus running smart_env_firmware.ino.hex and NO other program using COM2:
    python serial_link_check.py [--port COM2]
"""

import argparse, time
import serial


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", default="COM2")
    a = ap.parse_args()
    with serial.Serial(a.port, 9600, timeout=1) as ser:
        ser.reset_input_buffer()
        modes = []
        for cmd in ["FAN:ON"] * 4 + ["FAN:OFF"] * 4:
            ser.write((cmd + "\n").encode())
            line = ser.readline().decode("utf-8", "ignore").strip()
            if not line:
                line = ser.readline().decode("utf-8", "ignore").strip()
            f = line.split(",")
            mode = f[7] if len(f) == 8 else ("old firmware (7 fields)" if len(f) == 7 else "?")
            modes.append(mode)
            print(f"sent {cmd:8} | Arduino says fan={f[6] if len(f) > 6 else '?':3} mode={mode}")
            time.sleep(0.5)
    if "AI" in modes:
        print("\nOK: the Arduino is receiving commands (PC -> Arduino works).")
    elif any("old" in m for m in modes):
        print("\nProteus is running the OLD firmware. Load Arduino/smart_env_firmware/build/smart_env_firmware.ino.hex.")
    else:
        print("\nFAIL: data comes in, but commands do not reach the Arduino."
              "\n - Wire COMPIM RXD -> Arduino RX (D0)"
              "\n - COMPIM: physical AND virtual baud = 9600"
              "\n - Close other programs using COM2")


if __name__ == "__main__":
    main()
