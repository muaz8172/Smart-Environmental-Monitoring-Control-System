"""
Name   : Muhammad Muaz Bin Md Fazli
Uni    : UniKL MFI
Topic  : Smart Environmental & Monitoring System
Two-way Serial <-> MQTT bridge (Arduino <-> Mosquitto <-> Node-RED / AI brain)

Usage  : python serial_mqtt_bridge.py [--port COM2] [--simulate]
Needs  : pip install pyserial paho-mqtt
"""

import argparse, json, logging, random, threading, time
import paho.mqtt.client as mqtt
import serial

log = logging.getLogger("bridge")
SER, LOCK, SIMULATE = None, threading.Lock(), False
SIM = {"cmd": None, "t": 0.0}  # last command seen by the simulator


def parse(frame):
    p = [x.strip().upper() for x in frame.split(",")]
    if len(p) == 7:
        p.append("LOCAL")
    if len(p) != 8 or p[6] not in ("ON", "OFF") or p[7] not in ("AI", "LOCAL"):
        return None
    try:
        t, h, pr, d, l, dist = map(float, p[:6])
    except ValueError:
        return None
    if any(v != v for v in (t, h, pr, d, l, dist)):  # skip "nan" from failed sensor
        return None
    return {"temperature": round(t, 2), "humidity": round(h, 2), "pressure": round(pr, 2),
            "dust": round(d, 2), "light": int(l), "distance": round(dist, 2),
            "fan_state": 1 if p[6] == "ON" else 0, "mode": p[7]}


def write_cmd(cmd):
    cmd = cmd.strip().upper()
    if SIMULATE:
        SIM.update(cmd=cmd, t=time.time())
        return True
    with LOCK:
        if SER is None or not SER.is_open:
            log.warning("Serial not open, dropped command %s", cmd)
            return False
        try:
            SER.write((cmd + "\n").encode())
            return True
        except Exception as e:  # never let a write error kill the MQTT thread
            log.error("Serial write failed (%s)", e)
            return False


def serial_frames(port, baud):
    global SER
    while True:
        try:
            with serial.Serial(port, baud, timeout=1) as ser:
                ser.reset_input_buffer()
                SER = ser
                log.info("Serial %s opened at %d baud", port, baud)
                while True:
                    if raw := ser.readline():
                        yield raw.decode("utf-8", "ignore").strip()
        except serial.SerialException as e:
            SER = None
            log.error("Serial %s unavailable (%s), retrying in 3 s", port, e)
            time.sleep(3)


def simulated_frames(interval=2):
    s, fan = {"t": 31.0, "h": 50.0, "p": 1010.0, "d": 35.0, "l": 650.0, "dist": 60.0}, "OFF"
    lim = {"t": (25, 42), "h": (25, 75), "p": (975, 1055), "d": (10, 80), "l": (300, 900), "dist": (20, 150)}
    while True:  # slow random walk; a running fan cools the room
        cool = fan == "ON"
        for k, lo, hi in (("t", -0.08, 0.1), ("h", -0.15, 0.19), ("d", -0.5, 0.53), ("p", -0.5, 0.5), ("l", -15, 15)):
            s[k] += random.uniform(lo, hi) - (cool * {"t": 0.4, "h": 0.9, "d": 1.8}.get(k, 0))
        s["dist"] = random.choice((60.0, 140.0)) if random.random() < 0.03 else s["dist"] + random.uniform(-2, 2)
        s = {k: min(max(v, lim[k][0]), lim[k][1]) for k, v in s.items()}
        t, h, p, d, l, dist = s["t"], s["h"], s["p"], s["d"], int(s["l"]), s["dist"]
        if SIM["cmd"] in ("FAN:ON", "FAN:OFF") and time.time() - SIM["t"] < 10:  # same 10 s watchdog as Arduino
            fan, mode = SIM["cmd"][4:], "AI"
        else:
            fan = "ON" if dist < 100 and (t >= 37 or h >= 60 or d >= 55 or p >= 1050 or l <= 500) else "OFF"
            mode = "LOCAL"
        yield f"{t:.2f},{h:.2f},{p:.2f},{d:.2f},{l},{dist:.2f},{fan},{mode}"
        time.sleep(interval)


def main():
    global SIMULATE
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", default="COM2")
    ap.add_argument("--baud", type=int, default=9600)
    ap.add_argument("--broker", default="localhost")
    ap.add_argument("--mqtt-port", type=int, default=1883)
    ap.add_argument("--topic", default="muaz/iot/mfi")  # must match Node-RED "mqtt in"
    ap.add_argument("--simulate", action="store_true")
    a = ap.parse_args()
    SIMULATE = a.simulate
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s",
                        datefmt="%d/%m/%Y %H:%M:%S")

    def on_connect(c, *x):
        log.info("MQTT connected (%s)", x[2])
        c.subscribe(a.topic + "/cmd")

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="python-serial-bridge")
    client.on_connect = on_connect
    client.on_disconnect = lambda *x: log.warning("MQTT disconnected (%s), reconnecting...", x[3])
    client.on_message = lambda *x: write_cmd(x[2].payload.decode(errors="ignore"))
    client.reconnect_delay_set(1, 10)
    client.connect_async(a.broker, a.mqtt_port, 60)
    client.loop_start()
    time.sleep(1)

    frames = simulated_frames() if a.simulate else serial_frames(a.port, a.baud)
    log.info("Publishing to '%s' (Ctrl+C to stop)", a.topic)
    try:
        for frame in frames:
            data = parse(frame)
            if data is None:
                log.warning("Skipped invalid frame: %r", frame)
            elif client.publish(a.topic, json.dumps(data)).rc == mqtt.MQTT_ERR_SUCCESS:
                log.info("Published %s", data)
            else:
                log.error("Publish failed (broker not connected)")
    except KeyboardInterrupt:
        log.info("Stopped by user")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
