"""
Name   : Muhammad Muaz Bin Md Fazli
Uni    : UniKL MFI
Topic  : Smart Environmental & Monitoring System
Module : 4 - Serial-to-MQTT bridge (Arduino -> Mosquitto -> Node-RED)

Usage  : python Module_4_MQTT_Mosquitto.py [--port COM2] [--simulate]
Needs  : pip install pyserial paho-mqtt
"""

import argparse, json, logging, random, time
import paho.mqtt.client as mqtt
import serial

log = logging.getLogger("bridge")


def parse(frame):
    p = [x.strip() for x in frame.split(",")]
    if len(p) != 7 or p[6].upper() not in ("ON", "OFF"):
        return None
    try:
        t, h, pr, d, l, dist = map(float, p[:6])
    except ValueError:
        return None
    if any(v != v for v in (t, h, pr, d, l, dist)):  # skip "nan" from failed sensor
        return None
    return {"temperature": round(t, 2), "humidity": round(h, 2), "pressure": round(pr, 2),
            "dust": round(d, 2), "light": int(l), "distance": round(dist, 2),
            "fan_state": 1 if p[6].upper() == "ON" else 0}


def serial_frames(port, baud):
    while True:
        try:
            with serial.Serial(port, baud, timeout=1) as ser:
                ser.reset_input_buffer()
                log.info("Serial %s opened at %d baud", port, baud)
                while True:
                    if raw := ser.readline():
                        yield raw.decode("utf-8", "ignore").strip()
        except serial.SerialException as e:
            log.error("Serial %s unavailable (%s), retrying in 3 s", port, e)
            time.sleep(3)


def simulated_frames():
    while True:
        t, h, p, d = random.uniform(28, 40), random.uniform(35, 70), random.uniform(970, 1060), random.uniform(20, 70)
        l, dist = random.randint(300, 900), random.uniform(20, 150)
        fan = "ON" if dist < 100 and (t >= 37 or h >= 60 or d >= 55 or p >= 1050 or l <= 500) else "OFF"
        yield f"{t:.2f},{h:.2f},{p:.2f},{d:.2f},{l},{dist:.2f},{fan}"
        time.sleep(2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", default="COM2")
    ap.add_argument("--baud", type=int, default=9600)
    ap.add_argument("--broker", default="localhost")
    ap.add_argument("--mqtt-port", type=int, default=1883)
    ap.add_argument("--topic", default="muaz/iot/mfi")  # must match Node-RED "mqtt in"
    ap.add_argument("--simulate", action="store_true")
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s",
                        datefmt="%d/%m/%Y %H:%M:%S")

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="python-serial-bridge")
    client.on_connect = lambda *x: log.info("MQTT connected (%s)", x[3])
    client.on_disconnect = lambda *x: log.warning("MQTT disconnected (%s), reconnecting...", x[3])
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
