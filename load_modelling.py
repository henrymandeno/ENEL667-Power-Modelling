import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from FestivalPower import Festival, Stage

RESIDENTIAL_HOMES = 400
SUMMER_END_DATE = '2023-04-15 00:00:00'

# pd.set_option("display.max_colwidth", None)
# pd.set_option("display.max_rows", None)

# Define input/output data files
RNA_SET_TIMES_FILE = 'Input Data/RNA Set Times.xlsx'
CARDRONA_LOAD_FILE = 'Input Data/Cardrona Load.xlsx'
HOUSEHOLD_LOAD_FILE = 'Input Data/Household Load.xlsx'
OUTPUT_LOAD_FILE = 'Output Data/Annual Load.xlsx'


def rna_initialise_stages(festival):
    """ Calculates estimated RNA load """

    # Load set times
    stage_set_times = pd.read_excel(RNA_SET_TIMES_FILE)
    alpine_area_set_times = stage_set_times.iloc[:, 0:2]
    sonarchy_set_times = stage_set_times.iloc[:, 3:5]
    log_cabin_set_times = stage_set_times.iloc[:, 6:8]
    boom_box_set_times = stage_set_times.iloc[:, 9:11]
    camp_set_times = stage_set_times.iloc[:, 12:14]

    # Instantiate stages
    alpine_area_stage = Stage('Alpine Area', speakers=60, lights=40, schedule=alpine_area_set_times)
    sonarchy_stage = Stage('Sonarchy', speakers=40, lights=30, schedule=sonarchy_set_times)
    log_cabin_stage = Stage('Log Cabin', speakers=10, lights=20, schedule=log_cabin_set_times)
    boom_box_stage = Stage('Boom Box', speakers=10, lights=10, schedule=boom_box_set_times)
    camp_stage = Stage('Camp', speakers=22, lights=15, schedule=camp_set_times)

    # Add stages to festival
    festival.add_stage(alpine_area_stage)
    festival.add_stage(sonarchy_stage)
    festival.add_stage(log_cabin_stage)
    festival.add_stage(boom_box_stage)
    festival.add_stage(camp_stage)

def model_rna_load():

    rna_festival = Festival('RNA', ticketing_stands=4, food_stands=20, drink_stands=10, toilet_stands=5, campervan_outlets=40, lights=100)

    rna_initialise_stages(rna_festival)

    rna_power = rna_festival.calculate_festival_power()

    rna_peak_power = rna_festival.calculate_peak_festival_power()

    return rna_power


def combine_cardrona_load(rna_power):

    cardrona = pd.read_excel(CARDRONA_LOAD_FILE)

    cardrona.columns = ['datetime', 'KW']
    rna_power.columns = ['datetime', 'KW']

    combined_power = cardrona.merge(rna_power, on='datetime', how='left')

    combined_power = combined_power.rename(columns={'KW_x': 'Cardrona KW'})
    combined_power = combined_power.rename(columns={'KW_y': 'RNA KW'})

    return combined_power

def model_residential_load():

    cardrona = pd.read_excel(CARDRONA_LOAD_FILE)
    household = pd.read_excel(HOUSEHOLD_LOAD_FILE)

    # Retrieve half-hourly household data, multiply by number of homes to supply, convert to kW
    household_summer = pd.concat([household.iloc[:, 0], household.iloc[:, 1] * RESIDENTIAL_HOMES / 1000], axis=1) 
    household_summer.columns = ['Time', 'KW']
    household_winter = pd.concat([household.iloc[:, 3], household.iloc[:, 4] * RESIDENTIAL_HOMES / 1000], axis=1)
    household_winter.columns = ['Time', 'KW']

    residential_load = cardrona.iloc[:, 0] # Retrieve datetime format for 1st column
    
    summer_end_datetime = pd.to_datetime(SUMMER_END_DATE) # Threshold for summer/winter household power change

    # Filter times based on the datetime condition
    cardrona['Datetime'] = pd.to_datetime(cardrona.iloc[:, 0])
    summer_times = cardrona.loc[cardrona['Datetime'] < summer_end_datetime, 'Datetime']
    winter_times = cardrona.loc[cardrona['Datetime'] >= summer_end_datetime, 'Datetime']

    # Merge based on the condition (datetime1 < threshold_datetime)
    summer_load = pd.merge(summer_times, household_summer, left_on=summer_times.dt.time, right_on='Time', how='left')
    winter_load = pd.merge(winter_times, household_winter, left_on=winter_times.dt.time, right_on='Time', how='left')
    
    residential_load = pd.concat([summer_load, winter_load], axis=0)
    residential_load = residential_load.drop('Time', axis=1)

    return residential_load

def combine_residential_load(rna_and_cardrona_power, residential_load):

    residential_load.columns = ['datetime', 'KW']

    combined_power = rna_and_cardrona_power.merge(residential_load, on='datetime', how='left')

    combined_power = combined_power.rename(columns={'KW': 'Residential KW'})

    combined_power['Total KW'] = 0
    combined_power['Total KW'] += combined_power['Cardrona KW'] + combined_power['RNA KW'].fillna(0) + combined_power['Residential KW']

    return combined_power

def display_results(total_power):
    
    # total_power.plot('datetime', 'Cardrona KW')
    # total_power.plot('datetime', 'RNA KW')
    # total_power.plot('datetime', 'Residential KW')
    # total_power.plot('datetime', 'Total KW')

    print('Cardrona Peak Power: {:.2f} KW'.format(total_power['Cardrona KW'].max()))
    print('RNA Peak Power: {:.2f} KW'.format(total_power['RNA KW'].max()))
    print('Residential Peak Power: {:.2f} KW'.format(total_power['Residential KW'].max()))
    print('Overall Peak Power: {:.2f} KW'.format(total_power['Total KW'].max()))
    # plt.show()

def write_output(total_power):

    total_power.to_excel(OUTPUT_LOAD_FILE, sheet_name='Sheet1')

def calculate_average_daily_energy(load):
    """Calculates average energy consumption per day based on a years data"""
    daily_energy_array = []
    daily_energy_sum = 0
    counter = 1
    for index, row in load.iterrows():
        load_half_hourly = row['Total KW']
        daily_energy_sum += load_half_hourly * 0.5 
        if counter == 48:
            counter = 0
            daily_energy_array.append(daily_energy_sum)
            daily_energy_sum = 0
        counter += 1

    total_energy = 0
    for i in range(len(daily_energy_array)):
        total_energy += daily_energy_array[i]

    average_daily_energy = (total_energy / len(daily_energy_array)) / 1000
    print("Daily energy consumption average: {:.2f} KWh".format(average_daily_energy))

def calculate_annual_load():

    rna_power = model_rna_load()

    rna_and_cardrona_power = combine_cardrona_load(rna_power)

    residential_load = model_residential_load()

    total_power = combine_residential_load(rna_and_cardrona_power, residential_load)

    display_results(total_power)

    # write_output(total_power)

    return total_power

