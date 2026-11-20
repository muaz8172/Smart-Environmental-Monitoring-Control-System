"""
Name   : Muhammad Muaz Bin Md Fazli
Uni    : UniKL MFI
Topic  : Smart Environmental & Monitoring System
Checks the PC -> Arduino direction on COM2 (Proteus COMPIM RXD -> Arduino RX).
Run with Proteus running smart_env_firmware.ino.hex and NO other program using COM2:
    python serial_link_check.py [--port COM2]
Virtual port pair test (stop Proteus first so COM1 is free):
    python serial_link_check.py --pair [--other COM1]
"""

import argparse, time
import serial


def pair_check(pc, sim):
    with serial.Serial(sim, 9600, timeout=1) as a, serial.Serial(pc, 9600, timeout=1) as b:
        for x in (a, b):
            x.reset_input_buffer()
        b.write(b"PC->ARDUINO test\n"); time.sleep(0.5); down = a.read(a.in_waiting or 1)
        a.write(b"ARDUINO->PC test\n"); time.sleep(0.5); up = b.read(b.in_waiting or 1)
    print(f"{pc} -> {sim} (commands to Arduino):", "OK" if b"PC->ARDUINO" in down else f"FAILED, got {down!r}")
    print(f"{sim} -> {pc} (sensor data to PC):  ", "OK" if b"ARDUINO->PC" in up else f"FAILED, got {up!r}")
    if b"PC->ARDUINO" not in down:
        print("\nThe virtual port pair only works one way. In VSPE, the device must be type 'Pair' (COM1 <-> COM2).")


def echo_check(port):
    with serial.Serial(port, 9600, timeout=1) as ser:
        ser.reset_input_buffer()
        seen, end = [], time.time() + 6
        ser.write(b"HELLO\n")
        while time.time() < end:
            line = ser.readline().decode("utf-8", "ignore").strip()
            if line:
                seen.append(line); print("Arduino says:", line)
            if "ECHO:HELLO" in line:
                break
    if any("ECHO:HELLO" in s for s in seen):
        print("\nOK: the Arduino RX pin receives data. Load smart_env_firmware.ino.hex again and rerun without --echo.")
    elif any(s.startswith("READY") for s in seen):
        print("\nFAIL: Arduino -> PC works but the Arduino never received HELLO."
              "\n - The COMPIM RXD wire does not reach the MCU RX pin in this Arduino model."
              "\n - Try the bare ATMEGA328P part, or check the Arduino library model's RX pin.")
    else:
        print("\nNo READY lines: is serial_echo_test.ino.hex loaded and the simulation running?")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", default="COM2")
    ap.add_argument("--pair", action="store_true", help="test the virtual COM pair itself (Proteus stopped)")
    ap.add_argument("--other", default="COM1")
    ap.add_argument("--echo", action="store_true", help="test with Arduino/serial_echo_test firmware loaded in Proteus")
    a = ap.parse_args()
    if a.pair:
        return pair_check(a.port, a.other)
    if a.echo:
        return echo_check(a.port)
    with serial.Serial(a.port, 9600, timeout=1) as ser:
        ser.reset_input_buffer()
        modes = []
        for cmd in ["FAN:ON"] * 4 + ["FAN:OFF"] * 4:
            ser.write((cmd + "\n").encode())
            line, end = "", time.time() + 5  # one Arduino loop can take 2-4 s
            while time.time() < end and len(line.split(",")) < 7:
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
