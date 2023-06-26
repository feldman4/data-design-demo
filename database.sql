-- Table for raw data
CREATE TABLE RawData (
    site_id INTEGER PRIMARY KEY,
    nd2_file TEXT,
    frame_index INTEGER,
    channel_name TEXT,
    plate TEXT,
    well TEXT
);

-- Table for experimental conditions
CREATE TABLE ExperimentalConditions (
    plate TEXT,
    well TEXT,
    condition_name TEXT,
    condition_value TEXT,
    PRIMARY KEY (plate, well, condition_name)
);

-- Table for segmented cells
CREATE TABLE SegmentedCells (
    cell_id INTEGER PRIMARY KEY,
    plate TEXT,
    well TEXT,
    site_id INTEGER,
    FOREIGN KEY (plate, well) REFERENCES ExperimentalConditions (plate, well),
    FOREIGN KEY (site_id) REFERENCES RawData (site_id)
);

-- Table for per-cell scalar features
CREATE TABLE ScalarFeatures (
    cell_id INTEGER,
    feature_name TEXT,
    value REAL,
    FOREIGN KEY (cell_id) REFERENCES SegmentedCells (cell_id)
);

-- Table for per-cell vector features
CREATE TABLE VectorFeatures (
    cell_id INTEGER,
    feature_name TEXT,
    vector BLOB,
    FOREIGN KEY (cell_id) REFERENCES SegmentedCells (cell_id)
);
