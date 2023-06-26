import hashlib
import inspect
import sqlite3

import cv2
import fire
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from skimage import measure

from demo.mock import load_image_from_nd2_file, segment_nuclear_stain


def segment_and_store(database_name, site_id, nuclear_stain_channel='DAPI', nucleus_diameter=30):
    """
    Segment the cells in a given site based on a nuclear stain channel and store the segmentation results in an SQLite database.

    :param database_name: Name of the SQLite database.
    :param site_id: ID of the site for segmentation.
    :param nuclear_stain_channel: Name of the nuclear stain channel. Default is 'DAPI'.
    :param nucleus_diameter: Expected diameter of the nuclei for segmentation. Default is 30 pixels.
    """
    # Connect to the SQLite database
    conn = sqlite3.connect(database_name)
    c = conn.cursor()

    # Fetch the raw data needed for segmentation
    c.execute(f'SELECT nd2_file, frame_index FROM RawData WHERE site_id = "{site_id}" AND channel_name = "{nuclear_stain_channel}"')
    nd2_file, frame_index = c.fetchone()

    # Perform cell segmentation
    image = load_image_from_nd2_file(nd2_file, frame_index)
    labels = segment_nuclear_stain(image, nucleus_diameter)

    # Loop through each unique cell in the segmented image
    for cell_id in np.unique(labels):
        # Skip the background
        if cell_id == 0:
            continue

        # Create a mask for the current cell
        mask = labels == cell_id
        binary_mask = mask.tobytes()  # Convert numpy array to binary

        # Calculate bounding box properties
        y_nonzero, x_nonzero = np.nonzero(mask)
        bbox_height = y_nonzero.max() - y_nonzero.min()
        bbox_width = x_nonzero.max() - x_nonzero.min()
        top_left_x = x_nonzero.min()
        top_left_y = y_nonzero.min()

        # Fetch plate and well data related to the site
        c.execute(f'SELECT plate, well FROM RawData WHERE site_id = "{site_id}"')
        plate, well = c.fetchone()
        
        # Insert data into SegmentedCells table
        c.execute('INSERT INTO SegmentedCells (cell_id, plate, well, site_id) VALUES (?, ?, ?, ?)',
                  (cell_id, plate, well, site_id))
        # Insert the cell mask into VectorFeatures
        c.execute('INSERT INTO VectorFeatures (cell_id, feature_name, vector) VALUES (?, ?, ?)',
                  (cell_id, 'mask', binary_mask))
        # Insert the bounding box properties into ScalarFeatures
        c.execute('INSERT INTO ScalarFeatures (cell_id, feature_name, value) VALUES (?, ?, ?)',
                  (cell_id, 'bbox_height', bbox_height))
        c.execute('INSERT INTO ScalarFeatures (cell_id, feature_name, value) VALUES (?, ?, ?)',
                  (cell_id, 'bbox_width', bbox_width))
        c.execute('INSERT INTO ScalarFeatures (cell_id, feature_name, value) VALUES (?, ?, ?)',
                  (cell_id, 'top_left_x', top_left_x))
        c.execute('INSERT INTO ScalarFeatures (cell_id, feature_name, value) VALUES (?, ?, ?)',
                  (cell_id, 'top_left_y', top_left_y))

    # Commit the changes and close the connection
    conn.commit()
    conn.close()



# Main function for cell segmentation and storing the results
def segment_cells(database_name, site_id, channel_name='DAPI', nucleus_diameter=30):
    # Connect to the SQLite database
    with sqlite3.connect(database_name) as conn:
        # Create a cursor object
        cur = conn.cursor()

        # Query the required data for the specified site_id and channel_name
        cur.execute("SELECT nd2_file, frame_index FROM RawData WHERE site_id = ? AND channel_name = ?",
                    (site_id, channel_name))
        res = cur.fetchone()
        if res is None:
            raise ValueError("No data found for site_id {} and channel {}".format(site_id, channel_name))

        nd2_file, frame_index = res

        # Load the image
        image = load_image_from_nd2_file(nd2_file, frame_index)

        # Perform segmentation
        label_mask = segment_nuclear_stain(image, nucleus_diameter)

        # Use regionprops from skimage to analyze the label mask
        props = measure.regionprops(label_mask)

        # Query the plate and well for the specified site_id
        cur.execute("SELECT plate, well FROM RawData WHERE site_id = ?", (site_id,))
        res = cur.fetchone()
        if res is None:
            raise ValueError("No plate and well data found for site_id {}".format(site_id))

        plate, well = res

        # Loop over each property (cell) in props
        for prop in props:
            # Insert data into the SegmentedCells table
            cur.execute("INSERT INTO SegmentedCells (plate, well, site_id) VALUES (?, ?, ?)", (plate, well, site_id))
            cell_id = cur.lastrowid

            # Calculate and store bounding box parameters as vector features
            minr, minc, maxr, maxc = prop.bbox
            bbox_height = maxr - minr
            bbox_width = maxc - minc
            bbox_vector = np.array([bbox_height, bbox_width, minr, minc], dtype=np.uint32).tobytes()
            cur.execute("INSERT INTO VectorFeatures (cell_id, feature_name, vector) VALUES (?, ?, ?)",
                        (cell_id, 'bbox', bbox_vector))

            # Create and store the mask for the current cell as a vector feature
            mask_vector = prop.image.astype(np.uint8).tobytes()
            cur.execute("INSERT INTO VectorFeatures (cell_id, feature_name, vector) VALUES (?, ?, ?)",
                        (cell_id, 'mask', mask_vector))

        # Commit the changes
        conn.commit()


# this function led us to a problem with the original sql layout (cell_id integer vs string that can store long hashes)
def segment_cells(database_name, site_id, channel_name='DAPI', nucleus_diameter=30):
    # Connect to the SQLite database
    with sqlite3.connect(database_name) as conn:
        # Create a cursor object
        cur = conn.cursor()

        # Query the required data for the specified site_id and channel_name
        cur.execute("SELECT nd2_file, frame_index FROM RawData WHERE site_id = ? AND channel_name = ?",
                    (site_id, channel_name))
        res = cur.fetchone()
        if res is None:
            raise ValueError("No data found for site_id {} and channel {}".format(site_id, channel_name))

        nd2_file, frame_index = res

        # Load the image
        image = load_image_from_nd2_file(nd2_file, frame_index)

        # Perform segmentation
        label_mask = segment_nuclear_stain(image, nucleus_diameter)

        # Use regionprops from skimage to analyze the label mask
        props = measure.regionprops(label_mask)

        # Query the plate and well for the specified site_id
        cur.execute("SELECT plate, well FROM RawData WHERE site_id = ?", (site_id,))
        res = cur.fetchone()
        if res is None:
            raise ValueError("No plate and well data found for site_id {}".format(site_id))

        plate, well = res

        # Loop over each property (cell) in props
        for prop in props:
            # Calculate bounding box parameters
            minr, minc, maxr, maxc = prop.bbox
            bbox_height = maxr - minr
            bbox_width = maxc - minc
            bbox_vector = np.array([bbox_height, bbox_width, minr, minc], dtype=np.uint32).tobytes()

            # Create a unique hash from the site_id and bounding box, then convert it to an integer and truncate to 64 bits
            cell_id = int(hashlib.sha256(f"{site_id}{bbox_vector}".encode()).hexdigest(), 16) & ((1 << 64) - 1)

            # Insert data into the SegmentedCells table
            cur.execute("INSERT INTO SegmentedCells (cell_id, plate, well, site_id) VALUES (?, ?, ?, ?)", 
                        (cell_id, plate, well, site_id))

            # Store the bounding box parameters as vector features
            cur.execute("INSERT INTO VectorFeatures (cell_id, feature_name, vector) VALUES (?, ?, ?)",
                        (cell_id, 'bbox', bbox_vector))

            # Create and store the mask for the current cell as a vector feature
            mask_vector = prop.image.astype(np.uint8).tobytes()
            cur.execute("INSERT INTO VectorFeatures (cell_id, feature_name, vector) VALUES (?, ?, ?)",
                        (cell_id, 'mask', mask_vector))

        # Commit the changes
        conn.commit()

from skimage import measure
import numpy as np

def segment_cells(database_name, site_id, channel_name='DAPI', nucleus_diameter=30):
    # Connect to the SQLite database
    with sqlite3.connect(database_name) as conn:
        # Create a cursor object
        cur = conn.cursor()

        # Query the required data for the specified site_id and channel_name
        cur.execute("SELECT nd2_file, frame_index FROM RawData WHERE site_id = ? AND channel_name = ?",
                    (site_id, channel_name))
        res = cur.fetchone()
        if res is None:
            raise ValueError("No data found for site_id {} and channel {}".format(site_id, channel_name))

        nd2_file, frame_index = res

        # Load the image
        image = load_image_from_nd2_file(nd2_file, frame_index)

        # Perform segmentation
        label_mask = segment_nuclear_stain(image, nucleus_diameter)

        # Use regionprops from skimage to analyze the label mask
        props = measure.regionprops(label_mask)

        # Query the plate and well for the specified site_id
        cur.execute("SELECT plate, well FROM RawData WHERE site_id = ?", (site_id,))
        res = cur.fetchone()
        if res is None:
            raise ValueError("No plate and well data found for site_id {}".format(site_id))

        plate, well = res

        # Loop over each property (cell) in props
        for prop in props:
            # Insert data into the SegmentedCells table
            cur.execute("INSERT INTO SegmentedCells (plate, well, site_id) VALUES (?, ?, ?)", (plate, well, site_id))
            cell_id = cur.lastrowid

            # Calculate and store bounding box parameters as scalar features
            minr, minc, maxr, maxc = prop.bbox
            bbox_height = maxr - minr
            bbox_width = maxc - minc
            cur.execute("INSERT INTO ScalarFeatures (cell_id, feature_name, value) VALUES (?, ?, ?)",
                        (cell_id, 'bbox_height', bbox_height))
            cur.execute("INSERT INTO ScalarFeatures (cell_id, feature_name, value) VALUES (?, ?, ?)",
                        (cell_id, 'bbox_width', bbox_width))
            cur.execute("INSERT INTO ScalarFeatures (cell_id, feature_name, value) VALUES (?, ?, ?)",
                        (cell_id, 'bbox_origin_x', minc))
            cur.execute("INSERT INTO ScalarFeatures (cell_id, feature_name, value) VALUES (?, ?, ?)",
                        (cell_id, 'bbox_origin_y', minr))

            # Store bounding box parameters as vector features as well
            bbox_vector = np.array([bbox_height, bbox_width, minr, minc], dtype=np.uint32).tobytes()
            cur.execute("INSERT INTO VectorFeatures (cell_id, feature_name, vector) VALUES (?, ?, ?)",
                        (cell_id, 'bbox', bbox_vector))

            # Create and store the mask for the current cell as a vector feature
            mask_vector = prop.image.astype(np.uint8).tobytes()
            cur.execute("INSERT INTO VectorFeatures (cell_id, feature_name, vector) VALUES (?, ?, ?)",
                        (cell_id, 'mask', mask_vector))

        # Commit the changes
        conn.commit()



def get_cell_info(database_name, cell_ids):
    # Connect to the SQLite database
    conn = sqlite3.connect(database_name)

    # Query to get the information for the cells
    query = """
        SELECT 
            SegmentedCells.cell_id, 
            SegmentedCells.site_id,
            RawData.nd2_file,
            RawData.frame_index,
            RawData.channel_name,
            ScalarFeatures.feature_name,
            ScalarFeatures.value
        FROM SegmentedCells
        JOIN RawData ON SegmentedCells.site_id = RawData.site_id
        JOIN ScalarFeatures ON SegmentedCells.cell_id = ScalarFeatures.cell_id
        WHERE SegmentedCells.cell_id IN ({})
        AND ScalarFeatures.feature_name IN ('bbox_height', 'bbox_width', 'bbox_x', 'bbox_y')
    """.format(", ".join(map(str, cell_ids)))

    # Execute the query and fetch the results
    cursor = conn.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()

    # Close the connection
    conn.close()

    # Convert the rows to a more usable format
    cell_info = {cell_id: {} for cell_id in cell_ids}
    for row in rows:
        cell_id, site_id, nd2_file, frame_index, channel_name, feature_name, value = row
        cell_info[cell_id].setdefault('site_id', site_id)
        cell_info[cell_id].setdefault('nd2_file', nd2_file)
        cell_info[cell_id].setdefault('frame_index', frame_index)
        cell_info[cell_id].setdefault('channel_name', channel_name)
        cell_info[cell_id][feature_name] = value

    return cell_info


def get_cell_info(database_name, cell_ids):
    # Connect to the SQLite database
    conn = sqlite3.connect(database_name)

    # Query to get the information for the cells
    query = """
        SELECT 
            SegmentedCells.cell_id, 
            SegmentedCells.site_id,
            RawData.nd2_file,
            RawData.frame_index,
            RawData.channel_name,
            ScalarFeatures.feature_name,
            ScalarFeatures.value
        FROM SegmentedCells
        JOIN RawData ON SegmentedCells.site_id = RawData.site_id
        JOIN ScalarFeatures ON SegmentedCells.cell_id = ScalarFeatures.cell_id
        WHERE SegmentedCells.cell_id IN ({})
        AND ScalarFeatures.feature_name IN ('bbox_height', 'bbox_width', 'bbox_origin_x', 'bbox_origin_y')
    """.format(", ".join(map(str, cell_ids)))

    # Execute the query and fetch the results
    cursor = conn.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()

    # Close the connection
    conn.close()

    # Check that data was returned
    if not rows:
        raise ValueError(f"No data found in database for cell_ids: {cell_ids}")

    # Convert the rows to a more usable format
    cell_info = {cell_id: {} for cell_id in cell_ids}
    for row in rows:
        cell_id, site_id, nd2_file, frame_index, channel_name, feature_name, value = row
        if cell_id not in cell_info:
            raise ValueError(f"Unexpected cell_id {cell_id} found in database")

        cell_info[cell_id].setdefault('site_id', site_id)
        cell_info[cell_id].setdefault('nd2_file', nd2_file)
        cell_info[cell_id].setdefault('frame_index', frame_index)
        cell_info[cell_id].setdefault('channel_name', channel_name)
        cell_info[cell_id][feature_name] = value

    return cell_info



def show_cell_montage(database_name, cell_ids):
    # Get cell info from the database
    cell_info = get_cell_info(database_name, cell_ids)

    # Load and display images for each cell
    for cell_id, info in cell_info.items():
        image = load_image_from_nd2_file(info['nd2_file'], info['frame_index'])
        bbox_x, bbox_y, bbox_width, bbox_height = info['bbox_origin_x'], info['bbox_origin_y'], info['bbox_width'], info['bbox_height']

        cell_image = image[int(bbox_y):int(bbox_y+bbox_height), int(bbox_x):int(bbox_x+bbox_width)]
        
        # Add some padding to better visualize the cell
        cell_image = cv2.copyMakeBorder(cell_image, 10, 10, 10, 10, cv2.BORDER_CONSTANT)

        plt.imshow(cell_image, cmap='gray')
        plt.title(f"Cell ID: {cell_id}, Channel: {info['channel_name']}")
        plt.show()


def get_local_functions():
    current_module = inspect.currentframe().f_back.f_globals
    local_functions = []

    for name, obj in current_module.items():
        if inspect.isfunction(obj) and obj.__module__ == __name__:
            local_functions.append(name)

    return local_functions


def main():
    local_functions = get_local_functions()
    cli = fire.Fire({func: globals()[func] for func in local_functions})

if __name__ == "__main__":
    main()
