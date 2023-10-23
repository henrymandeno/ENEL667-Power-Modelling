import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from load_modelling import calculate_annual_load, calculate_average_daily_energy
from generation_modelling import calculate_annual_generation
from storage_and_grid_modelling import calculate_storage_and_grid_usage

def get_total_load(load):
    """Returns Total KW column of annual load dataframe"""

    total_power = load[['datetime', 'Total KW']]

    return total_power

def reorder_generation(generation):
    split_index = 23424 # September 1st index

    # Split the DataFrame into two parts
    top_half = generation.iloc[:split_index]
    top_half = top_half.drop(index=range(5664, 5664 + 4 * 24)).reset_index(drop=True) #Gets rid of Feb 29th (2023 not a leap year)
    top_half['Month-Date-Time'] = pd.to_datetime('2023-' + top_half['Month-Date-Time'], format='%Y-%m-%d %H:%M:%S')

    bottom_half = generation.iloc[split_index:]
    bottom_half.iloc[:, 0] = pd.to_datetime('2022-' + bottom_half['Month-Date-Time'], format='%Y-%m-%d %H:%M:%S')

    # Concatenate the two parts in reverse order to reorder the rows
    reordered_generation = pd.concat([bottom_half, top_half], ignore_index=True)
    
    return reordered_generation


if __name__ == "__main__":

    print("-------------- Load Statistics ---------------")
    load_data = calculate_annual_load()
    annual_load = get_total_load(load_data)
    calculate_average_daily_energy(annual_load)

    print("----------- Generation Statistics ------------")
    annual_generation = calculate_annual_generation()
    annual_generation = reorder_generation(annual_generation)

    # annual_generation.to_excel('Output Data/Annual Generation 3 x 2.0MW.xlsx', sheet_name='Sheet1')

    # fig, ax = plt.subplots(figsize=(8, 6))
    # annual_load.plot(0, 1, ax=ax, label='Annual Load')
    # annual_generation.plot(0, 1, ax=ax, label='Annual Generation')
    # ax.set_title('Annual Load and Generation')
    # ax.legend()

    print("-------------- Energy Storage ----------------")
    calculate_storage_and_grid_usage(annual_load, annual_generation)

    plt.show()