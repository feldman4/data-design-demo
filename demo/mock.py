import pandas as pd
import numpy as np
import random
import string
import os
import numpy as np
from skimage.filters import threshold_otsu
from skimage.measure import label


import numpy as np
import tifffile

def open_tif_image(filepath):
    try:
        image_data = tifffile.imread(filepath)
        if len(image_data.shape) != 2:
            raise ValueError("Input image is not 2D.")
        return np.array(image_data)
    except FileNotFoundError:
        print("File not found.")
    except Exception as e:
        print("An error occurred:", str(e))


def load_image_from_nd2_file(nd2_file, site_index):
    """Load from a single DAPI tif instead.
    """
    return open_tif_image('data/example.tif')


def segment_nuclear_stain(image, diameter):
    return threshold_and_label(image)


def threshold_and_label(image_array):
    # Apply thresholding
    threshold_value = threshold_otsu(image_array)
    binary_image = image_array > threshold_value

    # Generate label mask
    labeled_image = label(binary_image)

    return labeled_image


def generate_mock_data():
    # Define parameters
    plates = ['plate_'+str(i) for i in range(1, 9)] # 8 plates
    wells = [f'{chr(65+i)}{str(j).zfill(2)}' for i in range(8) for j in range(1, 13)] # 96 wells (8 rows x 12 columns)
    cell_lines = ['Hep2G', 'A549']
    compounds = ['Compound_A', 'Compound_B', 'Compound_C', 'No_compound']
    channels = ['DAPI', 'GFP', 'mitotracker']
    
    image_data = []
    conditions = []

    for plate in plates:
        for well in wells:
            cell_line = np.random.choice(cell_lines)
            compound = np.random.choice(compounds)
            
            # add condition data
            conditions.append([plate, well, 'cell line', cell_line])
            conditions.append([plate, well, 'compound', compound])
            
            for channel in channels:
                site_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))  # random string of length 10 as site_id
                nd2_file = f'{plate}_{well}_{channel}.nd2' 
                frame_index = random.randint(0,100) # random frame index
                
                # add image data
                image_data.append([site_id, nd2_file, frame_index, channel, plate, well])

    # Convert lists to dataframes
    df_image_data = pd.DataFrame(image_data, columns=['site_id', 'nd2_file', 'frame_index', 'channel_name', 'plate', 'well'])
    df_conditions = pd.DataFrame(conditions, columns=['plate', 'well', 'condition_name', 'condition_value'])

    # Save dataframes to csv
    df_image_data.to_csv('image_data.csv', index=False)
    df_conditions.to_csv('conditions.csv', index=False)
    
    print(f'Data generated and saved in {os.getcwd()}')

