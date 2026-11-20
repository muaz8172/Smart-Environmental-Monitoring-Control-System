# Muhammad Muaz Bin Md Fazli, UniKL MFI, topic: Smart Environmental & Monitoring System
import serial_mqtt_bridge as br


def test_parse_8(): assert br.parse("34,57,980.12,51,509,97.86,ON,AI")["mode"] == "AI"
def test_parse_7_default(): assert br.parse("34,57,980.12,51,509,97.86,OFF")["mode"] == "LOCAL"
def test_parse_bad_mode(): assert br.parse("34,57,980,51,509,97,ON,XX") is None


def test_write_cmd_no_port():
    br.SER, br.SIMULATE = None, False
    assert br.write_cmd("FAN:ON") is False


def test_sim_follows_cmd():
    br.SIMULATE = True
    br.write_cmd("FAN:ON")
    f = next(br.simulated_frames(interval=0)).split(",")
    assert f[6] == "ON" and f[7] == "AI"


def test_write_cmd_unexpected_error():
    class Broken:
        is_open = True
        def write(self, _): raise OSError("device gone")
    br.SER, br.SIMULATE = Broken(), False
    assert br.write_cmd("FAN:ON") is False
