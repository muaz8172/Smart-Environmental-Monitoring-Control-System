# Muhammad Muaz Bin Md Fazli, UniKL MFI, topic: Smart Environmental & Monitoring System
import ai_brain as ai

N = ai.NORMAL


def rows(key, start, step, n=30):
    return [{**N, key: start + i * step} for i in range(n)]


def test_score_normal(): assert ai.health_score(N) == 100
def test_score_drops(): assert ai.health_score({**N, "temperature": 40, "humidity": 70}) < ai.health_score({**N, "temperature": 40}) < 100
def test_score_floor(): assert ai.health_score({**N, "temperature": 80, "humidity": 100, "dust": 900, "light": 0, "pressure": 300}) >= 0
def test_forecast_eta(): assert abs(ai.forecast(rows("humidity", 50, 0.2), "humidity", 60) - 0.7) < 0.05
def test_forecast_short_history(): assert ai.forecast(rows("humidity", 50, 1, 4), "humidity", 60) is None
def test_forecast_flat(): assert ai.forecast(rows("humidity", 50, 0), "humidity", 60) is None
def test_forecast_falling(): assert ai.forecast(rows("humidity", 59, -0.1), "humidity", 60) is None
def test_forecast_too_far(): assert ai.forecast(rows("humidity", 30, 0.001), "humidity", 60) is None
def test_spike(): assert any("spike" in a for a in ai.anomalies(N, {**N, "temperature": 36}))
def test_small_click_no_spike(): assert ai.anomalies(N, {**N, "humidity": 52}) == []
def test_fault(): assert any("fault" in a for a in ai.anomalies(None, {**N, "humidity": 140}))
def test_old_rule_light(): assert ai.old_rule({**N, "light": 400}) and not ai.old_rule({**N, "light": 400, "distance": 150})


def run(b, rs): return [b.step(r) for r in rs][-1]


def test_preemptive_on():
    out = run(ai.Brain(), rows("humidity", 50, 0.2))
    assert out["fan"] == "ON" and "early" in out["reason"]


def test_light_not_fan():
    out = run(ai.Brain(), [{**N, "light": 300}] * 3)
    assert out["fan"] == "OFF" and out["alerts"]


def test_hysteresis():
    b = ai.Brain(); b.step({**N, "temperature": 38})
    assert b.step(N)["fan"] == "ON" and b.step(N)["fan"] == "OFF"


def test_unoccupied_off():
    b = ai.Brain(); b.step({**N, "temperature": 38})
    assert b.step({**N, "temperature": 38, "distance": 150})["fan"] == "OFF"


def test_override_beats_unoccupied():
    b = ai.Brain(); b.set_override("ON")
    out = b.step({**N, "distance": 150})
    assert out["fan"] == "ON" and out["mode"] == "HUMAN" and out["would"] == "OFF" and b.command() == "FAN:ON"


def test_override_normalise():
    b = ai.Brain(); b.set_override("on"); b.set_override("xyz")
    assert b.override == "ON"


def test_missing_mode_key(): assert ai.Brain().step(dict(N))["fan"] == "OFF"


def test_energy_saved():
    out = run(ai.Brain(), [{**N, "light": 300}] * 1800)
    assert abs(out["energy"]["old_wh"] - 5) < 0.01 and out["energy"]["ai_wh"] == 0 and out["energy"]["saved_wh"] > 0


def test_events_on_flip():
    b = ai.Brain()
    assert any(t == "DECISION" for t, _ in b.step({**N, "temperature": 38})["events"])
    assert b.step({**N, "temperature": 38})["events"] == []


def test_forecast_needs_10_readings():
    assert ai.forecast(rows("dust", 35, 1, 9), "dust", 55) is None and ai.forecast(rows("dust", 35, 1, 10), "dust", 55) is not None


def test_bad_payload_does_not_poison_history():
    import pytest
    b = ai.Brain()
    with pytest.raises((KeyError, ValueError, TypeError)):
        b.step({k: v for k, v in N.items() if k != "humidity"})
    assert all(b.step(N)["fan"] == "OFF" for _ in range(12))


def test_string_numbers_accepted(): assert ai.Brain().step({**N, "temperature": "38"})["fan"] == "ON"


def test_override_energy_not_counted_as_ai():
    b = ai.Brain(); b.set_override("ON")
    out = run(b, [N] * 10)
    assert out["energy"]["ai_wh"] == 0


def test_status_short_labels():
    assert ai.Brain().step(N)["status"] == "All normal"
    assert ai.Brain().step({**N, "distance": 150})["status"] == "Room empty"
    assert ai.Brain().step({**N, "humidity": 65})["status"] == "Too humid"
    assert run(ai.Brain(), rows("humidity", 50, 0.2))["status"] == "Pre-cooling"
    b = ai.Brain(); b.set_override("OFF")
    assert b.step(N)["status"] == "Manual override"


def test_status_cooling_down():
    b = ai.Brain(); b.step({**N, "temperature": 38})
    assert b.step(N)["status"] == "Cooling down"


def test_alarm_levels_with_deadband():
    assert ai.alarm_level("temperature", 34) == 0
    assert ai.alarm_level("temperature", 35.5) == 1           # warning
    assert ai.alarm_level("temperature", 37.2) == 2           # high-priority alarm
    assert ai.alarm_level("temperature", 36.7, prev=2) == 2   # inside 0.5 deadband, stays in alarm
    assert ai.alarm_level("temperature", 36.4, prev=2) == 1
    assert ai.alarm_level("light", 480) == 2 and ai.alarm_level("humidity", 33) == 1


def test_alarm_events_and_list():
    b = ai.Brain()
    out = b.step({**N, "temperature": 38})
    assert ("ALARM" in [t for t, _ in out["events"]]) and out["alarms"][0]["tag"] == "temperature" and out["alarms"][0]["priority"] == "HIGH"
    out = b.step(N)
    assert any(t == "CLEARED" for t, _ in out["events"]) and out["alarms"][0]["rtn"] and not out["alarms"][0]["ack"]


def test_ack_logged_not_override():
    b = ai.Brain(); b.set_override("ACK:temperature")
    out = b.step(N)
    assert b.override == "AUTO" and ("ACK", "Operator acknowledged temperature alarm") in out["events"]


def test_ack_is_kept_by_the_brain():
    b = ai.Brain(); assert b.step({**N, "temperature": 38})["alarms"][0]["ack"] is False
    b.set_override("ACK:TEMPERATURE")
    a = b.step({**N, "temperature": 38})["alarms"][0]
    assert a["ack"] is True and a["priority"] == "HIGH" and a["limit"] == 37


def test_escalation_needs_new_ack():
    b = ai.Brain(); b.step({**N, "temperature": 35.5}); b.set_override("ACK:temperature")
    assert b.step({**N, "temperature": 35.6})["alarms"][0]["ack"] is True
    a = b.step({**N, "temperature": 38})["alarms"][0]
    assert a["priority"] == "HIGH" and a["ack"] is False


def test_cleared_alarm_stays_until_acked():
    b = ai.Brain(); b.step({**N, "temperature": 38}); b.step(N)
    b.set_override("ACK:temperature")
    assert b.step(N)["alarms"] == []


def test_comfort_alarms_suppressed_when_room_empty():
    out = ai.Brain().step({**N, "light": 300, "distance": 150})
    assert out["alarms"] == [] and out["suppressed"] == ["light"] and not any(t == "ALARM" for t, _ in out["events"])


def test_pressure_alarm_not_suppressed():
    out = ai.Brain().step({**N, "pressure": 975, "distance": 150})
    assert out["alarms"][0]["tag"] == "pressure" and out["alarms"][0]["side"] == "low"


def test_override_expires_after_15_min():
    t = [1000.0]; b = ai.Brain(clock=lambda: t[0]); b.set_override("OFF")
    assert b.step(N)["override_left_s"] == 900
    t[0] += 899; assert b.step(N)["mode"] == "HUMAN"
    t[0] += 2; out = b.step(N)
    assert out["mode"] == "AI" and b.override == "AUTO" and out["override_left_s"] == 0 and any("expired" in m for _, m in out["events"])
