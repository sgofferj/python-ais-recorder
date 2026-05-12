-- Initial schema for AIS Recorder

CREATE TABLE IF NOT EXISTS positions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    mmsi INT NOT NULL,
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    INDEX ix_positions_timestamp (timestamp),
    INDEX ix_positions_mmsi (mmsi)
);

CREATE TABLE IF NOT EXISTS metadata (
    mmsi INT PRIMARY KEY,
    imo INT,
    vessel_name VARCHAR(255),
    last_seen DATETIME NOT NULL
);