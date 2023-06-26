import matplotlib.pyplot as plt
import numpy as np
import sqlite3
import inspect
import fire
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import os

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import os
from matplotlib.colors import ListedColormap, Normalize
import numpy as np

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import os
from matplotlib.colors import ListedColormap
import numpy as np

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import os
import seaborn as sns

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import os
import seaborn as sns


def visualize_experiment_conditions(database_name, output_directory):
    """
    Visualize experimental conditions for each plate in the SQLite database and save the plots in the specified output directory.

    :param database_name: Name of the SQLite database.
    :param output_directory: Directory path where the plots will be saved.
    """    # Ensure the output directory exists
    os.makedirs(output_directory, exist_ok=True)

    # Connect to the SQLite database
    conn = sqlite3.connect(database_name)
    cursor = conn.cursor()

    # Get unique plates and conditions from the database
    cursor.execute("SELECT DISTINCT plate FROM ExperimentalConditions")
    plates = [plate[0] for plate in cursor.fetchall()]  # unpack the tuples
    
    cursor.execute("SELECT DISTINCT condition_value FROM ExperimentalConditions")
    conditions = [condition[0] for condition in cursor.fetchall()]  # unpack the tuples
    
    # Create a color palette
    palette = sns.color_palette('hls', len(conditions))

    # Create a mapping of conditions to colors
    color_dict = {condition: palette[i] for i, condition in enumerate(conditions)}
    
    for plate in plates:
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Execute query to get all conditions on this plate
        cursor.execute("SELECT well, condition_value FROM ExperimentalConditions WHERE plate=?", (plate,))
        results = cursor.fetchall()
        
        # Convert the results to a DataFrame for easier manipulation
        df = pd.DataFrame(results, columns=['well', 'condition'])
        df['row'] = df['well'].apply(lambda x: ord(x[0]) - ord('A'))  # convert 'A'-'H' to 0-7
        df['column'] = df['well'].apply(lambda x: int(x[1:]) - 1)  # convert '01'-'12' to 0-11
        
        # Draw grid lines
        for x in range(13):
            ax.axvline(x-0.5, linestyle='-', color='black', linewidth=0.5)
        for y in range(9):
            ax.axhline(y-0.5, linestyle='-', color='black', linewidth=0.5)
        
        # Iterate over each condition to plot
        for i, condition in enumerate(conditions):
            condition_df = df[df['condition'] == condition]
            ax.scatter(condition_df['column'] + i*0.1, condition_df['row'] + i*0.1, color=color_dict[condition], label=condition)
        
        # Formatting
        ax.set_title(f'Plate {plate} Conditions')
        ax.set_xticks(range(12))
        ax.set_xticklabels(range(1, 13))  # 1-indexed column labels
        ax.set_yticks(range(8))
        ax.set_yticklabels([chr(i + ord('A')) for i in range(8)])  # 'A'-'H' row labels
        ax.invert_yaxis()  # invert the y-axis so that 'A' is on top
        ax.legend(title="Conditions", bbox_to_anchor=(1.05, 1), loc='upper left')  # place legend outside of plot
        fig.tight_layout()
        
        # Save the plot
        plt.savefig(os.path.join(output_directory, f'{plate}_conditions.png'))
        plt.close()  # close the figure to free up memory

    # Close the connection to the database
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
