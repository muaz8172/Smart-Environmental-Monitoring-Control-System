"""
Name   : Muhammad Muaz Bin Md Fazli
Uni    : UniKL MFI
Topic  : Smart Environmental & Monitoring System
Builds IR7_HTML_Dashboard.json (Node-RED import) from ir7_dashboard.html.
Run    : python build_ir7_flow.py   then in Node-RED: Ctrl+I -> select file -> Import -> Deploy
"""

import json
from pathlib import Path

HERE = Path(__file__).parent
BROKER = "fd80b27dfc9a2898"  # existing "Mosquitto" broker config node (localhost:1883)
DB = "50a196d0c453da90"      # existing sqlitedb config node -> Database/Sensor_database.db
TAB, WSL = "a17e0000000000a1", "a17e0000000000a2"


def node(i, t, x, y, wires=(), **kw):
    return {"id": f"a17e00000000{i:04x}", "type": t, "z": TAB, "x": x, "y": y,
            "wires": [[f"a17e00000000{w:04x}" for w in wires]] if wires is not None else [], **kw}


def build():
    html = (HERE / "ir7_dashboard.html").read_text(encoding="utf-8")
    to_ws = ("const d = typeof msg.payload === 'string' ? JSON.parse(msg.payload) : msg.payload;\n"
             "msg.payload = JSON.stringify({type: msg.topic.endsWith('/ai') ? 'ai' : 'sensor', data: d});\nreturn msg;")
    guard = ("const p = String(msg.payload).trim().toUpperCase();\n"
             "if (!['AUTO', 'ON', 'OFF'].includes(p) && !/^ACK:(TEMPERATURE|HUMIDITY|PRESSURE|DUST|LIGHT)$/.test(p)) return null;\n"
             "msg.payload = p;\nreturn msg;")
    return [
        {"id": TAB, "type": "tab", "label": "IR 7.0 Dashboard", "disabled": False,
         "info": "Muhammad Muaz Bin Md Fazli, UniKL MFI - open http://localhost:1880/ir7"},
        {"id": WSL, "type": "websocket-listener", "path": "/ws/ir7", "wholemsg": "false"},
        node(1, "http in", 140, 60, [2], name="GET /ir7", url="/ir7", method="get", upload=False, swaggerDoc=""),
        node(2, "template", 340, 60, [3], name="IR 7.0 page", field="payload", fieldType="msg", format="html",
             syntax="plain", template=html, output="str"),
        node(3, "http response", 540, 60, None, name="", statusCode="",
             headers={"content-type": "text/html; charset=utf-8"}),
        node(4, "mqtt in", 150, 140, [6], name="Sensor data", topic="muaz/iot/mfi", qos="0",
             datatype="auto-detect", broker=BROKER, nl=False, rap=True, rh=0, inputs=0),
        node(5, "mqtt in", 150, 200, [6], name="AI brain", topic="muaz/iot/mfi/ai", qos="0",
             datatype="auto-detect", broker=BROKER, nl=False, rap=True, rh=0, inputs=0),
        node(6, "function", 370, 170, [7], name="Tag for page", func=to_ws, outputs=1),
        node(7, "websocket out", 580, 170, None, name="ws /ws/ir7", server=WSL, client=""),
        node(8, "websocket in", 150, 280, [9], name="Override + alarm ACK", server=WSL, client=""),
        node(9, "function", 370, 280, [10], name="Override / ACK only", func=guard, outputs=1),
        node(10, "mqtt out", 600, 280, None, name="Override", topic="muaz/iot/mfi/override", qos="0",
             retain="false", broker=BROKER),
        node(11, "http in", 150, 360, [12], name="GET /ir7/events", url="/ir7/events", method="get",
             upload=False, swaggerDoc=""),
        node(12, "sqlite", 370, 360, [13], name="AI_Events", mydb=DB, sqlquery="fixed",
             sql="SELECT * FROM AI_Events ORDER BY ID DESC LIMIT 100;"),
        node(13, "http response", 580, 360, None, name="", statusCode="", headers={}),
    ]


if __name__ == "__main__":
    flow = build()
    (HERE / "IR7_HTML_Dashboard.json").write_text(json.dumps(flow, indent=2), encoding="utf-8")
    print(f"Wrote {len(flow)} nodes to IR7_HTML_Dashboard.json")
