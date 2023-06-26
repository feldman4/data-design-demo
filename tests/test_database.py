
from demo.database import create_database_from_schema, import_data_to_database

import os
import sqlite3
import tempfile
import pandas as pd

def test_create_database_from_schema():
    # Define the schema
    schema = '''
    CREATE TABLE Users (
        id INTEGER PRIMARY KEY,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT
    );
    '''

    # Create a temporary database file
    with tempfile.NamedTemporaryFile(suffix=".db") as temp_file:
        temp_db_file = temp_file.name

        # Create the database using the schema
        create_database_from_schema(temp_db_file, schema)

        # Verify that the database file exists
        assert os.path.exists(temp_db_file)

        # Connect to the database
        conn = sqlite3.connect(temp_db_file)
        cursor = conn.cursor()

        # Verify that the Users table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Users';")
        table_exists = cursor.fetchone()
        assert table_exists is not None

        # Verify the table structure
        cursor.execute("PRAGMA table_info('Users');")
        table_info = cursor.fetchall()
        expected_columns = [(0, 'id', 'INTEGER', 0, None, 1), (1, 'name', 'TEXT', 0, None, 0), (2, 'email', 'TEXT', 0, None, 0), (3, 'password', 'TEXT', 0, None, 0)]
        assert table_info == expected_columns

        # Close the database connection
        conn.close()

    print("Test passed successfully.")


def test_import_data_to_database():
    # Create mock dataframes for image data and conditions
    image_data = pd.DataFrame({
        'site_id': [1, 2, 3],
        'nd2_file': ['file1.nd2', 'file2.nd2', 'file3.nd2'],
        'frame_index': [0, 1, 2],
        'channel_name': ['DAPI', 'GFP', 'mCherry'],
        'plate': ['Plate1', 'Plate2', 'Plate2'],
        'well': ['A01', 'B02', 'C03']
    })

    conditions = pd.DataFrame({
        'plate': ['Plate1', 'Plate2'],
        'well': ['A01', 'B02'],
        'condition_name': ['Cell Line', 'Treatment'],
        'condition_value': ['HEK293', 'Control']
    })

    # Specify the paths for the mock data CSV files and the database
    image_data_path = 'image_data_mock.csv'
    conditions_path = 'conditions_mock.csv'
    database_path = 'project_database.db'

    # Save the mock dataframes to CSV files
    image_data.to_csv(image_data_path, index=False)
    conditions.to_csv(conditions_path, index=False)

    # Import the mock data to the database
    import_data_to_database(database_path, image_data_path, conditions_path)

    # Verify that the import was successful by querying the database
    conn = sqlite3.connect(database_path)
    query = '''
    SELECT *
    FROM ExperimentalConditions
    '''
    result = pd.read_sql_query(query, conn)
    conn.close()

    print(result)

    # Cleanup the temporary files
    os.remove(image_data_path)
    os.remove(conditions_path)
    os.remove(database_path)
