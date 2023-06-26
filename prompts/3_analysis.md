1. Please write a function to select site_ids from the database that match specific conditions, or plate names, or well names. 

2. Please write a function to segment cells and store the results. Required arguments are the database name, and a single site_id. Optional arguments are the channel name with nuclear stain (default is DAPI) and an expected nucleus diameter (default is 30). It can use these functions:
- load_image_from_nd2_file(nd2_file, frame_index), returns a 2D numpy array
- segment_nuclear_stain(image, diameter), returns a 2D array of integer labels
https://chat.openai.com/share/8281d4f4-853c-4b68-b167-dddf1bd0c4e1


@rubric and @api
3. Please write a function to load raw data and show an image montage for a list of cells. The arguments are the database name and a list of cell IDs. 
