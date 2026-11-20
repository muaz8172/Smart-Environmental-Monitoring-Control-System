"""
Name   : Muhammad Muaz Bin Md Fazli
Uni    : UniKL MFI
Topic  : Smart Environmental & Monitoring System
IR 7.0 AI brain (predict, decide, explain, override, energy)

Usage  : python ai_brain.py [--broker localhost] [--topic muaz/iot/mfi]
"""

import argparse, json, logging, sqlite3, time
from pathlib import Path
import paho.mqtt.client as mqtt

log = logging.getLogger("ai-brain")
DB = Path(__file__).resolve().parent.parent / "Database" / "Sensor_database.db"

# key: (low, high, scale) comfort band; None = no limit on that side
BANDS = {"temperature": (None, 37, 5), "humidity": (30, 60, 10), "dust": (None, 55, 20),
         "pressure": (980, 1050, 30), "light": (500, None, 200)}
SPIKE = {"temperature": 5, "humidity": 15, "dust": 30}
RANGE = {"temperature": (-10, 80), "humidity": (0, 100), "pressure": (300, 1100),
         "dust": (0, 1000), "light": (0, 1023), "distance": (0, 500)}
STUCK_CHECK = False
NORMAL = {"temperature": 30, "humidity": 50, "pressure": 1010, "dust": 30, "light": 700, "distance": 50}


def health_score(r):
    penalty = 0
    for k, (lo, hi, scale) in BANDS.items():
        out = lo - r[k] if lo is not None and r[k] <= lo else r[k] - hi if hi is not None and r[k] >= hi else None
        if out is not None:
            penalty += min(20, 10 + 10 * out / scale)
    return max(0, round(100 - penalty))


def forecast(history, key, limit):
    ys = [h[key] for h in history[-30:]]
    n = len(ys)
    if n < 10 or ys[-1] >= limit:  # need 20 s of data for a stable trend
        return None
    xm, ym = (n - 1) / 2, sum(ys) / n
    slope = sum((x - xm) * (y - ym) for x, y in enumerate(ys)) / sum((x - xm) ** 2 for x in range(n))
    if slope <= 0:
        return None
    eta = (limit - ys[-1]) / (slope * 30)  # 30 readings per minute
    return round(eta, 2) if eta <= 10 else None


def anomalies(prev, r):
    out = [f"{k} sensor fault ({r[k]})" for k, (lo, hi) in RANGE.items() if not lo <= r[k] <= hi]
    if prev:
        out += [f"sudden spike in {k} ({prev[k]} -> {r[k]})" for k, s in SPIKE.items() if abs(r[k] - prev[k]) > s]
    return out


def old_rule(r):
    return r["distance"] < 100 and (r["temperature"] >= 37 or r["humidity"] >= 60 or r["dust"] >= 55
                                    or r["pressure"] >= 1050 or r["light"] <= 500)


TRIGGERS = {"temperature": 37, "humidity": 60, "dust": 55}  # fan-fixable only
UNITS = {"temperature": " °C", "humidity": " %", "dust": ""}
SHORT = {"temperature": "Too hot", "humidity": "Too humid", "dust": "Poor air"}
COMFORT = ("temperature", "humidity", "dust", "light")
# alarm limits (IEC 62682 rationalized): low alarm, low warning, high warning, high alarm, deadband
LIMITS = {"temperature": (None, None, 35, 37, 0.5), "humidity": (30, 35, 55, 60, 1), "pressure": (980, 985, 1045, 1050, 1),
          "dust": (None, None, 50, 55, 2), "light": (500, 550, None, None, 10)}


def alarm_level(tag, v, prev=0):
    la, lw, hw, ha, db = LIMITS[tag]
    past = lambda th, high, lvl: th is not None and (v >= th - (db if prev >= lvl else 0) if high else v <= th + (db if prev >= lvl else 0))
    return 2 if past(ha, True, 2) or past(la, False, 2) else 1 if past(hw, True, 1) or past(lw, False, 1) else 0
FAN_POWER_W = 5
OVERRIDE_MAX_S = 900  # manual override returns to AI after 15 min (IEC 62682: bypasses are time-limited)
GRID_KG_PER_KWH = 0.758  # Peninsular Malaysia grid emission factor (Suruhanjaya Tenaga) - verify latest value


class Brain:
    def __init__(self, clock=time.time):
        self.clock, self.override_since = clock, 0.0
        self.history, self.override, self.fan, self.would, self.clear = [], "AUTO", False, False, 0
        self.ai_wh = self.old_wh = 0.0
        self.last_anoms, self.events, self.alarm = [], [], {}

    def set_override(self, p):
        p = str(p).strip().upper()
        if p.startswith("ACK:") and p[4:].lower() in LIMITS:
            t, a = p[4:].lower(), self.alarm.get(p[4:].lower())
            if a:
                a["ack"] = True
                if a["rtn"]:
                    del self.alarm[t]  # cleared + acknowledged = gone
            self.events.append(("ACK", f"Operator acknowledged {t} alarm"))
            return
        if p in ("AUTO", "ON", "OFF") and p != self.override:
            self.override, self.override_since = p, self.clock()
            self.events.append(("OVERRIDE", f"Human set fan control to {p}"))

    def command(self):
        return "FAN:ON" if self.fan else "FAN:OFF"

    def step(self, r, dt_s=2):
        r = {k: float(r[k]) for k in NORMAL}  # validate before touching history
        if self.override != "AUTO" and self.clock() - self.override_since >= OVERRIDE_MAX_S:
            self.override = "AUTO"
            self.events.append(("OVERRIDE", "Manual override expired after 15 min: AI control restored"))
        prev = self.history[-1] if self.history else None
        self.history = (self.history + [r])[-30:]
        fc = {k: e for k, lim in TRIGGERS.items() if (e := forecast(self.history, k, lim)) is not None}
        soon = {k: e for k, e in fc.items() if e <= 3}
        over = [k for k, lim in TRIGGERS.items() if r[k] >= lim]
        occupied = r["distance"] < 100

        if not occupied:
            would, why, status = False, "room unoccupied", "Room empty"
        elif over:
            k = over[0]
            would, why, status = True, f"{k} {r[k]:.1f}{UNITS[k]} over {TRIGGERS[k]}{UNITS[k]}", SHORT[k]
        elif soon:
            k = min(soon, key=soon.get)
            would, why = True, f"{k} {r[k]:.1f}{UNITS[k]} rising, will exceed {TRIGGERS[k]}{UNITS[k]} in ~{soon[k]} min, cooling early"
            status = "Pre-cooling"
        else:
            would, why, status = False, "all fan-fixable readings normal", "All normal"
        if would:
            self.clear = 0
        elif self.would and occupied:
            self.clear += 1
            if self.clear < 2:
                would, why, status = True, "holding until readings stay normal", "Cooling down"
        self.would = would

        w = "ON" if would else "OFF"
        if self.override == "AUTO":
            fan, reason = would, f"Fan {w}: {why}."
        else:
            fan = self.override == "ON"
            status = "Manual override"
            reason = f"HUMAN OVERRIDE (fan {self.override}). AI would turn it {w}: {why}."
        if fan != self.fan:
            self.events.append(("DECISION", reason))
        self.fan = fan

        anoms = anomalies(prev, r)
        self.events += [("ANOMALY", a) for a in anoms if a not in self.last_anoms]
        self.last_anoms = anoms
        alerts = ([f"Low light ({r['light']})"] if r["light"] <= 500 else []) + \
                 ([f"Pressure out of range ({r['pressure']} hPa)"] if not 980 < r["pressure"] < 1050 else []) + \
                 ([f"Low humidity ({r['humidity']} %)"] if r["humidity"] <= 30 else [])

        suppressed = []  # IEC 62682 state-based alarming: comfort alarms mean nothing in an empty room
        for t in LIMITS:
            a = self.alarm.get(t)
            new = alarm_level(t, r[t], a["level"] if a and not a["rtn"] else 0)
            la, lw, hw, ha, _ = LIMITS[t]
            side = "high" if la is None or (ha is not None and r[t] >= (la + ha) / 2) else "low"
            lim = (ha if side == "high" else la) if new == 2 else (hw if side == "high" else lw)
            if new and not occupied and t in COMFORT:
                suppressed.append(t)
                if a and not a["rtn"]:
                    self.events.append(("SUPPRESSED", f"{t} alarm suppressed: room empty"))
                self.alarm.pop(t, None)
            elif new and (not a or a["rtn"] or new > a["level"]):
                self.alarm[t] = {"level": new, "ack": False, "rtn": False, "since": time.strftime("%H:%M:%S"), "value": r[t], "side": side, "limit": lim}
                self.events.append(("ALARM" if new == 2 else "WARNING", f"{'Alarm' if new == 2 else 'Warning'}: {t} {r[t]:g} {'>=' if side == 'high' else '<='} {lim}"))
            elif new:
                a.update(level=new, value=r[t], side=side, limit=lim)
            elif a and not a["rtn"]:
                self.events.append(("CLEARED", f"Cleared: {t} back to normal ({r[t]:g})"))
                if a["ack"]:
                    del self.alarm[t]
                else:
                    a.update(rtn=True, value=r[t])
        alarms = [{"tag": t, "priority": "HIGH" if a["level"] == 2 else "WARNING", **{k: a[k] for k in ("value", "side", "limit", "since", "ack", "rtn")}}
                  for t, a in self.alarm.items()]

        h = dt_s / 3600 * FAN_POWER_W
        if self.override == "AUTO":  # compare AI vs old rule only while the AI is in charge
            self.ai_wh += h if fan else 0
            self.old_wh += h if old_rule(r) else 0
        saved = self.old_wh - self.ai_wh
        events, self.events = self.events, []
        return {"score": health_score(r), "forecast": fc, "anomalies": anoms, "alerts": alerts,
                "would": w, "fan": "ON" if fan else "OFF", "mode": "AI" if self.override == "AUTO" else "HUMAN",
                "reason": reason, "status": status, "alarms": alarms, "suppressed": suppressed, "events": events,
                "override_left_s": max(0, round(OVERRIDE_MAX_S - (self.clock() - self.override_since))) if self.override != "AUTO" else 0,
                "energy": {"ai_wh": round(self.ai_wh, 3), "old_wh": round(self.old_wh, 3),
                           "saved_wh": round(saved, 3), "co2_g": round(saved * GRID_KG_PER_KWH, 2)}}


def log_events(db_path, events):
    if not events:
        return
    try:
        with sqlite3.connect(db_path) as c:
            c.execute("CREATE TABLE IF NOT EXISTS AI_Events (ID INTEGER PRIMARY KEY AUTOINCREMENT, "
                      "Timestamp TEXT DEFAULT (datetime('now','localtime')), Type TEXT, Message TEXT)")
            c.executemany("INSERT INTO AI_Events (Type, Message) VALUES (?, ?)", events)
        c.close()
    except sqlite3.Error as e:
        log.error("AI_Events log failed (%s)", e)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--broker", default="localhost")
    ap.add_argument("--topic", default="muaz/iot/mfi")
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s",
                        datefmt="%d/%m/%Y %H:%M:%S")
    brain = Brain()
    log_events(DB, [("SYSTEM", "AI Brain started")])  # also creates AI_Events for the dashboard

    def on_connect(c, *x):
        log.info("MQTT connected (%s)", x[2])
        c.subscribe([(a.topic, 0), (a.topic + "/override", 0)])

    def on_message(c, u, m):
        try:
            if m.topic.endswith("/override"):
                brain.set_override(m.payload.decode(errors="ignore"))
                return
            out = brain.step(json.loads(m.payload))
        except (ValueError, KeyError, TypeError) as e:
            log.warning("Bad message on %s (%s)", m.topic, e)
            return
        events = out.pop("events")
        c.publish(a.topic + "/ai", json.dumps(out))
        c.publish(a.topic + "/cmd", brain.command())
        log_events(DB, events)
        log.info("%s | score %s | %s", brain.command(), out["score"], out["reason"])

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="python-ai-brain")
    client.on_connect, client.on_message = on_connect, on_message
    client.reconnect_delay_set(1, 10)
    client.connect_async(a.broker, 1883, 60)
    log.info("AI Brain running (Ctrl+C to stop)")
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        log.info("Stopped by user")


if __name__ == "__main__":
    main()
