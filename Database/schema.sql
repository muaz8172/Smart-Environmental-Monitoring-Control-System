-- Name   : Muhammad Muaz Bin Md Fazli
-- Uni    : UniKL MFI
-- Topic  : Smart Environmental & Monitoring System
-- Relational schema (3NF) for Database/Sensor_database.db. Safe to run again (Node-RED runs it on start).

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS Device (
    Device_ID INTEGER PRIMARY KEY,
    Model     TEXT NOT NULL UNIQUE,
    Interface TEXT NOT NULL,
    Pins      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS Sensor (
    Sensor_ID INTEGER PRIMARY KEY,
    Device_ID INTEGER NOT NULL REFERENCES Device(Device_ID),
    Name      TEXT NOT NULL UNIQUE,
    Unit      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS Alarm_Limit (
    Sensor_ID    INTEGER PRIMARY KEY REFERENCES Sensor(Sensor_ID),
    Low_Alarm    REAL,
    Low_Warning  REAL,
    High_Warning REAL,
    High_Alarm   REAL,
    Deadband     REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS Reading (
    Reading_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Timestamp  TEXT DEFAULT (datetime('now','localtime')),
    Fan_Status TEXT NOT NULL CHECK (Fan_Status IN ('ON', 'OFF')),
    Mode       TEXT CHECK (Mode IN ('AI', 'LOCAL'))
);

CREATE TABLE IF NOT EXISTS Reading_Value (
    Reading_ID INTEGER NOT NULL REFERENCES Reading(Reading_ID) ON DELETE CASCADE,
    Sensor_ID  INTEGER NOT NULL REFERENCES Sensor(Sensor_ID),
    Value      REAL NOT NULL,
    PRIMARY KEY (Reading_ID, Sensor_ID)
) WITHOUT ROWID;

CREATE TABLE IF NOT EXISTS Event_Type (
    Type        TEXT PRIMARY KEY,
    Description TEXT
);

CREATE TABLE IF NOT EXISTS AI_Events (
    ID        INTEGER PRIMARY KEY AUTOINCREMENT,
    Timestamp TEXT DEFAULT (datetime('now','localtime')),
    Type      TEXT NOT NULL REFERENCES Event_Type(Type),
    Sensor_ID INTEGER REFERENCES Sensor(Sensor_ID),
    Message   TEXT NOT NULL
);

INSERT OR IGNORE INTO Device VALUES
    (1, 'DHT11',   'Digital (single wire)', 'D4'),
    (2, 'BMP180',  'I2C',                   'A4 SDA, A5 SCL'),
    (3, 'PPD42',   'Pulse (low time)',      'D5'),
    (4, 'LDR',     'Analog',                'A1'),
    (5, 'HC-SR04', 'Ultrasonic',            'D11 trig, D12 echo');

INSERT OR IGNORE INTO Sensor VALUES
    (1, 1, 'Temperature', '°C'),
    (2, 1, 'Humidity',    '%'),
    (3, 2, 'Pressure',    'hPa'),
    (4, 3, 'Dust',        'index'),
    (5, 4, 'Light',       'ADC 0-1023'),
    (6, 5, 'Distance',    'cm');

-- IEC 62682 limits (same values as LIMITS in Python/ai_brain.py)
INSERT OR IGNORE INTO Alarm_Limit VALUES
    (1, NULL, NULL, 35,   37,   0.5),
    (2, 30,   35,   55,   60,   1),
    (3, 980,  985,  1045, 1050, 1),
    (4, NULL, NULL, 50,   55,   2),
    (5, 500,  550,  NULL, NULL, 10);

INSERT OR IGNORE INTO Event_Type VALUES
    ('SYSTEM',     'AI brain started or stopped'),
    ('DECISION',   'AI changed the fan decision'),
    ('ANOMALY',    'Sudden spike or sensor fault'),
    ('WARNING',    'Value passed a warning limit'),
    ('ALARM',      'Value passed an alarm limit'),
    ('CLEARED',    'Value back inside its limit'),
    ('SUPPRESSED', 'Comfort alarm suppressed: room empty'),
    ('ACK',        'Operator acknowledged an alarm'),
    ('OVERRIDE',   'Human override changed or expired');

-- One row per reading, in the same columns as the old Sensor_data table (used by the dashboards)
CREATE VIEW IF NOT EXISTS Sensor_data AS
SELECT r.Reading_ID, r.Timestamp,
       MAX(CASE v.Sensor_ID WHEN 1 THEN v.Value END) AS Temperature,
       MAX(CASE v.Sensor_ID WHEN 2 THEN v.Value END) AS Humidity,
       MAX(CASE v.Sensor_ID WHEN 3 THEN v.Value END) AS Pressure,
       MAX(CASE v.Sensor_ID WHEN 4 THEN v.Value END) AS Dust,
       MAX(CASE v.Sensor_ID WHEN 5 THEN v.Value END) AS Light,
       MAX(CASE v.Sensor_ID WHEN 6 THEN v.Value END) AS Distance,
       r.Fan_Status, r.Mode
FROM Reading r LEFT JOIN Reading_Value v ON v.Reading_ID = r.Reading_ID
GROUP BY r.Reading_ID;

-- INSERT INTO Sensor_data (...) splits one reading into Reading + Reading_Value rows
CREATE TRIGGER IF NOT EXISTS Sensor_data_insert INSTEAD OF INSERT ON Sensor_data
BEGIN
    INSERT INTO Reading (Timestamp, Fan_Status, Mode)
    VALUES (COALESCE(NEW.Timestamp, datetime('now','localtime')), NEW.Fan_Status, NEW.Mode);
    INSERT INTO Reading_Value (Reading_ID, Sensor_ID, Value)
    SELECT (SELECT MAX(Reading_ID) FROM Reading), s, v FROM (
        SELECT 1 AS s, NEW.Temperature AS v UNION ALL SELECT 2, NEW.Humidity UNION ALL
        SELECT 3, NEW.Pressure UNION ALL SELECT 4, NEW.Dust UNION ALL
        SELECT 5, NEW.Light UNION ALL SELECT 6, NEW.Distance)
    WHERE v IS NOT NULL;
END;
