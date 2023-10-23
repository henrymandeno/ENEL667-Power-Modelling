import pandas as pd
import numpy as np

#Input and Output files
WIND_DATA_FILE = 'Input Data/Wind Cardrona.csv'
POWER_CURVE_DATA_FILE = 'Input Data/Tubine Power Curve.xlsx'
OUTPUT_LOAD_FILE = 'Output Data/Annual Load.xlsx'
OUTPUT_ANNUAL_WIND_DATA = 'Output Data/Annual Wind Data.xlsx'
OUTPUT_ANNUAL_GENERATION_DATA = 'Output Data/Annual Generation Data.xlsx'

# --------------------- Possible solutions -------------------
WIND_TURBINE_MODEL = 'V90-2.0MW'
WIND_TURBINE_QUANTITY = 3
CUT_IN_SPEED_MS = 3
CUT_OUT_SPEED_MS = 25

WIND_TURBINE_MODEL = 'V150-4.2MW'
WIND_TURBINE_QUANTITY = 1
CUT_IN_SPEED_MS = 3
CUT_OUT_SPEED_MS = 23

# WIND_TURBINE_MODEL = 'V90-2.0MW'
# WIND_TURBINE_QUANTITY = 3
# CUT_IN_SPEED_MS = 3
# CUT_OUT_SPEED_MS = 25

def get_annual_load():
    """Reads Output Load file and returns Total KW annual load"""
    overall_power = pd.read_excel(OUTPUT_LOAD_FILE)
    total_power = overall_power['Total KW']
    
    return total_power

def process_wind_data():
    """Reads wind data file, performs averaging across years"""
    raw_wind_data = pd.read_csv(WIND_DATA_FILE)
    
    wind_data = pd.concat([raw_wind_data['Time'], raw_wind_data['Cardrona - Ridgeline Stn 15min: WindSpd_kph_mean[KPH]']], axis=1)
    
    # Add new column which just contains day/month time (becomes independent of year)
    wind_data['Time'] = pd.to_datetime(wind_data['Time'], dayfirst=True)
    wind_data['Month-Date-Time'] = wind_data['Time'].dt.strftime('%m-%d %H:%M:%S')

    # Remove anomolies (where sensor was not recording data)
    wind_data = wind_data[wind_data['Cardrona - Ridgeline Stn 15min: WindSpd_kph_mean[KPH]'] != 0]

    # Convert to ms from kph
    wind_data['Cardrona - Ridgeline Stn 15min: Wind Speed Mean (m/s)'] = wind_data['Cardrona - Ridgeline Stn 15min: WindSpd_kph_mean[KPH]'] / 3.6

    annual_mean = wind_data.groupby('Month-Date-Time')['Cardrona - Ridgeline Stn 15min: Wind Speed Mean (m/s)'].mean()

    # annual_mean.plot()

    return annual_mean

def read_power_curve():
    power_curve = pd.read_excel(POWER_CURVE_DATA_FILE)

    power_curve = dict(zip(power_curve.iloc[:, 0], power_curve[f'{WIND_TURBINE_MODEL} Power Output (KW)']))

    return power_curve


def round_to_nearest_half(number):
    # Multiply the number by 2 to work with integer values
    rounded_number = round(number * 2)
    
    # Divide by 2 to get back to the original scale
    return rounded_number / 2


def calculate_generation(wind_data, power_curve):
    """Calculates generation based on cut-in and cut-out speed, turbine power and number of turbines"""
    print("Wind Turbine model: {} Wind Turbine Quantity: {}".format(WIND_TURBINE_MODEL, WIND_TURBINE_QUANTITY))

    wind_data = pd.read_excel(OUTPUT_ANNUAL_WIND_DATA)

    # Determine when generating power (within cut-in and cut-out wind speed)
    wind_data.loc[:, 'Generating Power'] = np.where((wind_data['Cardrona - Ridgeline Stn 15min: Wind Speed Mean (m/s)'] >= CUT_IN_SPEED_MS) & (wind_data['Cardrona - Ridgeline Stn 15min: Wind Speed Mean (m/s)'] < CUT_OUT_SPEED_MS), 1, 0)
    
    percentage_time_generating = np.sum(wind_data['Generating Power'] / len(wind_data) * 100)
    print("Generating power {:.2f}% of time".format(percentage_time_generating))
    
    # Calculate generation based on turbine power and number of turbines
    generation = wind_data.iloc[:, [0, 1, 2]].copy()  # Copy the selected columns
    for (index, row) in generation.iterrows():
        wind_speed_rounded = round_to_nearest_half(row['Cardrona - Ridgeline Stn 15min: Wind Speed Mean (m/s)'])
        
        generation.iloc[index, 2] *= power_curve[wind_speed_rounded] * WIND_TURBINE_QUANTITY
    
    generation = generation.drop(columns=['Cardrona - Ridgeline Stn 15min: Wind Speed Mean (m/s)'])
    generation = generation.rename(columns={'Generating Power': 'Generation KW'})

    return generation


def write_output(data, file):
    """Write to Excel Speadsheet"""
    data.to_excel(file, sheet_name='Sheet1')


def calculate_annual_generation():

    wind_data = process_wind_data()

    # write_output(wind_data, OUTPUT_ANNUAL_WIND_DATA)

    turbine_power_curve = read_power_curve()

    annual_generation = calculate_generation(wind_data, turbine_power_curve)

    # write_output(annual_generation, OUTPUT_ANNUAL_GENERATION_DATA)

    return annual_generation