import sqlite3
import pandas as pd
import inspect
import fire


def create_database_from_schema(database_name, schema_file):
    """
    Creates a SQLite database and executes each statement in the schema.

    :param database_name: The name of the database to create or connect to.
    :param schema_file: The path to the file containing the SQL schema.
    """
    # Connect to the database or create a new one
    conn = sqlite3.connect(database_name)
    cursor = conn.cursor()

    # Check if the database exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    result = cursor.fetchall()
    database_exists = bool(result)

    with open(schema_file, 'r') as file:
        schema = file.read()

    if not database_exists:
        # Create the database by executing the first statement in the schema
        cursor.execute(schema.split(';')[0])

    # Execute the remaining statements in the schema
    for statement in schema.split(';')[1:]:
        if statement.strip() != '':
            cursor.execute(statement)

    # Commit the changes and close the connection
    conn.commit()
    conn.close()



def import_data_to_database(database_path, image_data_path, conditions_path):
    """
    Imports image data and conditions from CSV files to a SQLite database.

    :param database_path: The path to the SQLite database.
    :param image_data_path: The path to the image data CSV file.
    :param conditions_path: The path to the conditions CSV file.
    """
    # Read image data and conditions CSV files
    image_data = pd.read_csv(image_data_path)
    conditions = pd.read_csv(conditions_path)

    # Connect to the SQLite database
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    # Import image data to RawData table
    image_data.to_sql('RawData', conn, if_exists='replace', index=False)

    # Import conditions to ExperimentalConditions table
    conditions.to_sql('ExperimentalConditions', conn, if_exists='replace', index=False)

    # Check if all plate/well combinations in conditions.csv are present in image_data.csv
    query = '''
    SELECT DISTINCT plate, well
    FROM ExperimentalConditions
    WHERE (plate, well) NOT IN (
        SELECT DISTINCT plate, well
        FROM RawData
    )
    '''
    mismatched_combinations = cursor.execute(query).fetchall()

    if len(mismatched_combinations) > 0:
        print("Warning: The following plate/well combinations in conditions.csv are not present in image_data.csv:")
        for plate, well in mismatched_combinations:
            print(f"Plate: {plate}, Well: {well}")

    # Commit the changes and close the connection
    conn.commit()
    conn.close()


def summarize_database(database_path):
    """
    Summarize the contents of an SQLite database.

    :param database_path: Path to the SQLite database.
    """
    # Connect to the database
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    # Count the number of plates
    cursor.execute("SELECT COUNT(DISTINCT plate) FROM RawData")
    num_plates = cursor.fetchone()[0]

    # Count the number of unique well/plate combinations
    cursor.execute("SELECT COUNT(DISTINCT plate || well) FROM RawData")
    num_unique_combinations = cursor.fetchone()[0]

    # Count the number of conditions tested
    cursor.execute("SELECT COUNT(DISTINCT condition_name) FROM ExperimentalConditions")
    num_conditions = cursor.fetchone()[0]

    # Count the number of segmented cells
    cursor.execute("SELECT COUNT(*) FROM SegmentedCells")
    num_cells = cursor.fetchone()[0]

    # Count the number of scalar features
    cursor.execute("SELECT COUNT(DISTINCT feature_name) FROM ScalarFeatures")
    num_scalar_features = cursor.fetchone()[0]

    # Count the number of vector features
    cursor.execute("SELECT COUNT(DISTINCT feature_name) FROM VectorFeatures")
    num_vector_features = cursor.fetchone()[0]

    # Print the summary
    print("Database Summary:")
    print("-----------------")
    print(f"Number of plates: {num_plates}")
    print(f"Number of unique well/plate combinations: {num_unique_combinations}")
    print(f"Number of conditions tested: {num_conditions}")
    print(f"Number of segmented cells: {num_cells}")
    print(f"Number of scalar features: {num_scalar_features}")
    print(f"Number of vector features: {num_vector_features}")

    # Close the database connection
    conn.close()


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
