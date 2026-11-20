import sqlite3
import pytest
import relational_db as rdb

OLD = ("CREATE TABLE Sensor_data (Sensor_ID INTEGER PRIMARY KEY AUTOINCREMENT, Timestamp DATETIME, Temperature REAL, "
       "Humidity REAL, Pressure REAL, Dust REAL, Light REAL, Distance REAL, Fan_Status TEXT);"
       "CREATE TABLE AI_Events (ID INTEGER PRIMARY KEY AUTOINCREMENT, Timestamp TEXT, Type TEXT, Message TEXT);"
       "INSERT INTO Sensor_data VALUES (1, '2026-11-19 10:00:00', 31.4, 51, 1010.9, 36.8, 572, 59, '1');"
       "INSERT INTO Sensor_data VALUES (2, NULL, 30, 50, 1011, NULL, 600, 40, 'OFF');"
       "INSERT INTO AI_Events VALUES (1, '2026-11-19 10:00:01', 'ALARM', 'Alarm: humidity 61 >= 60');")


@pytest.fixture
def db(tmp_path):
    p = tmp_path / "t.db"
    sqlite3.connect(p).executescript(OLD)
    counts, bad = rdb.migrate(p)
    assert counts == {"Reading": 2, "Reading_Value": 11, "AI_Events": 1} and bad == []
    c = sqlite3.connect(p)
    c.execute("PRAGMA foreign_keys = ON")
    yield c
    c.close()


def test_old_rows_kept(db):
    assert db.execute("SELECT Temperature, Dust, Fan_Status FROM Sensor_data ORDER BY Reading_ID").fetchall() == \
        [(31.4, 36.8, "ON"), (30.0, None, "OFF")]
    assert db.execute("SELECT Type, Sensor_ID FROM AI_Events").fetchone() == ("ALARM", 2)


def test_view_insert_splits_reading(db):
    db.execute("INSERT INTO Sensor_data (Temperature, Humidity, Pressure, Dust, Light, Distance, Fan_Status, Mode) "
               "VALUES (32, 55, 1000, NULL, 700, 80, 'ON', 'AI')")
    rid = db.execute("SELECT MAX(Reading_ID) FROM Reading").fetchone()[0]
    assert db.execute("SELECT COUNT(*) FROM Reading_Value WHERE Reading_ID = ?", (rid,)).fetchone()[0] == 5
    assert db.execute("SELECT Humidity, Mode, Timestamp IS NOT NULL FROM Sensor_data WHERE Reading_ID = ?", (rid,)).fetchone() == (55, "AI", 1)


def test_foreign_keys_enforced(db):
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("INSERT INTO AI_Events (Type, Message) VALUES ('NOPE', 'x')")
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("INSERT INTO Reading_Value VALUES (999, 1, 1)")


def test_migrate_twice_is_safe(tmp_path):
    p = tmp_path / "t.db"
    sqlite3.connect(p).executescript(OLD)
    rdb.migrate(p)
    assert rdb.migrate(p)[0]["Reading"] == 2
