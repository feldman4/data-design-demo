I would like to build a database to keep track of multi-channel images of cells acquired by fluorescence microscopy. 

The raw data is described by a table called "image_data.csv" with one row per 2D image frame, and these columns:
- site_id: a unique identifier for one physical location where an image was acquired
- nd2_file: a large .nd2 file containing many image frames
- frame_index: the location of this image frame in the .nd2 file
- channel_name: the microscope channel used to acquire this frame (e.g., DAPI, GFP, mCherry)
- plate: the name of the microplate where the image was taken
- well: the name of the well on the plate where the image was taken (e.g., A01, H10)

The experimental conditions are described by a long-form table called "conditions.csv" with one row per well, with these columns:
- plate
- well
- condition_name (e.g., "cell line")
- condition_value (e.g., "HEK293")

The analysis workflow for this data is
0. select data to analyze based on experimental conditions
1. find cells in images by segmenting the nuclear channel and cytoplasmic channels 
2. calculate features for each cell, such as the mean fluorescence intensity in each channel
3. classify cells based on their features
4. visualize the relationship between experimental conditions and cell classes

The project database stores references to raw data, conditions, segmented cells, and per-cell features (both scalars and vectors). When a cell is segmented, these values are stored: bounding box height and width, x and y coordinates of the top left corner, and a binary string encoding a boolean mask.

Here is the schema

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
