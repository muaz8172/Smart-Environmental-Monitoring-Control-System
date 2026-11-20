"""
Name   : Muhammad Muaz Bin Md Fazli
Uni    : UniKL MFI
Topic  : Smart Environmental & Monitoring System
Turns Database/Sensor_database.db into the relational schema in Database/schema.sql (run once, Node-RED stopped).
A backup is saved first. Old Sensor_data / AI_Events rows are moved into the new tables.
Usage  : python relational_db.py [--db path]
"""

import argparse, shutil, sqlite3, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB, SCHEMA = ROOT / "Database" / "Sensor_database.db", ROOT / "Database" / "schema.sql"
COLS = ["Temperature", "Humidity", "Pressure", "Dust", "Light", "Distance"]  # Sensor_ID 1..6


def kind(c, name):
    r = c.execute("SELECT type FROM sqlite_master WHERE name = ?", (name,)).fetchone()
    return r and r[0]


def migrate(db):
    c = sqlite3.connect(db)
    c.execute("PRAGMA foreign_keys = OFF")
    with c:
        old_data = kind(c, "Sensor_data") == "table"
        old_ev = kind(c, "AI_Events") == "table" and "Sensor_ID" not in [r[1] for r in c.execute("PRAGMA table_info(AI_Events)")]
        c.execute("DROP TRIGGER IF EXISTS set_timestamp")
        if old_data:
            c.execute("ALTER TABLE Sensor_data RENAME TO Sensor_data_old")
        if old_ev:
            c.execute("ALTER TABLE AI_Events RENAME TO AI_Events_old")
    c.executescript(SCHEMA.read_text(encoding="utf-8"))
    with c:
        if old_data:
            c.execute("INSERT INTO Reading (Reading_ID, Timestamp, Fan_Status) SELECT Sensor_ID, Timestamp, "
                      "CASE WHEN UPPER(Fan_Status) IN ('ON', '1') THEN 'ON' ELSE 'OFF' END FROM Sensor_data_old")
            for i, col in enumerate(COLS, 1):
                c.execute(f"INSERT INTO Reading_Value SELECT Sensor_ID, {i}, {col} FROM Sensor_data_old WHERE {col} IS NOT NULL")
            c.execute("DROP TABLE Sensor_data_old")
        if old_ev:
            c.execute("INSERT OR IGNORE INTO Event_Type (Type) SELECT DISTINCT Type FROM AI_Events_old")
            c.execute("INSERT INTO AI_Events (ID, Timestamp, Type, Sensor_ID, Message) SELECT e.ID, e.Timestamp, e.Type, "
                      "(SELECT s.Sensor_ID FROM Sensor s WHERE e.Message LIKE '%' || s.Name || '%'), e.Message FROM AI_Events_old e")
            c.execute("DROP TABLE AI_Events_old")
    bad = c.execute("PRAGMA foreign_key_check").fetchall()
    counts = {t: c.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in ("Reading", "Reading_Value", "AI_Events")}
    c.close()
    return counts, bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(DB))
    db = Path(ap.parse_args().db)
    backup = db.with_name(f"{db.stem}_backup_{time.strftime('%Y%m%d_%H%M%S')}.db")
    shutil.copy2(db, backup)
    print("Backup:", backup)
    counts, bad = migrate(db)
    print("Done:", counts, "| foreign key problems:", bad or "none")


if __name__ == "__main__":
    main()
