import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# If using storage, define storage capacity
STORAGE_CAPACITY_KWH = 1000 # Set to 0 if don't use any storage
STORAGE_CHARGE_EFFICIENCY = 0.9
STORAGE_DISCHARGE_EFFICIENCY = 0.9

STORAGE_OUTPUT_FILE = 'Output Data/Annual Storage Usage.xlsx'
GRID_OUTPUT_FILE = 'Output Data/Annual Grid Usage.xlsx'

def write_output(data, file):
    """Write to Excel Speadsheet"""
    data.to_excel(file, sheet_name='Sheet1')

def calculate_storage_and_grid_usage(load, generation):
    """Calculates power and energy rating of storage needed"""
    storage_time_series = load.iloc[:, [0]].copy()  # Copy the selected columns
    storage_time_series['Stored Energy (KWH)'] = 0
    storage_time_series['Storage Power (KW)'] = 0
    peak_storage_power_kw = 0
    stored_energy_kwh = STORAGE_CAPACITY_KWH #Initialise energy storage at full capacity
    stored_energy_prev_kwh = stored_energy_kwh
    generation_index = 0

    grid = load.iloc[:, [0]].copy()  # Copy the selected columns
    grid['Grid Usage KWH'] = 0
    grid['Grid Usage KW'] = 0
    grid['Grid Supply KWH'] = 0
    grid['Grid Supply KW'] = 0

    energy_source = load.iloc[:, [0]].copy()  # Copy the selected columns
    energy_source['Load (KW)'] = load.iloc[:, [1]].copy()
    energy_source['Renewable Generation (KW)'] = 0
    energy_source['Storage (KW)'] = 0
    energy_source['Grid (KW)'] = 0

    above_counter = 0
    below_counter = 0
    matched_gen_load = load.copy()
    matched_gen_load['Difference'] = 0

    for index, row in load.iterrows():
        
        # If a datetime is not present in the load, skip the generation value until reach it
        while (row.iloc[0] != generation.iloc[generation_index, 0]):
            generation_index += 2
        
        load_half_hourly = row['Total KW']
        generation_half_hourly = generation.iloc[generation_index, 1]
        matched_gen_load.iloc[index, 2] = int(generation_half_hourly - load_half_hourly)

        # If generation is greater than the load, generation can handle the power supply
        if load_half_hourly < generation_half_hourly:

            energy_source.iloc[index, 2] = int(load_half_hourly)

            # If we are using storage and the storage is not full, store the excess there
            if STORAGE_CAPACITY_KWH > 0 and stored_energy_kwh < STORAGE_CAPACITY_KWH:

                stored_energy_kwh += STORAGE_CHARGE_EFFICIENCY * (generation_half_hourly - load_half_hourly) * 0.5

                # If this will exceed the storage capacity, fill it up and supply the remainder to the grid
                if stored_energy_kwh > STORAGE_CAPACITY_KWH:
                    grid.iloc[index, 3] = int(stored_energy_kwh - STORAGE_CAPACITY_KWH)
                    grid.iloc[index, 4] = int(2 * (stored_energy_kwh - STORAGE_CAPACITY_KWH))
                    stored_energy_kwh = STORAGE_CAPACITY_KWH

            # Otherwise supply it to the grid
            else:
                grid.iloc[index, 3] = int((generation_half_hourly - load_half_hourly) * 0.5)
                grid.iloc[index, 4] = int((generation_half_hourly - load_half_hourly))
            
            above_counter += 1

        # If generation is less than load, need energy storage/grid to supply the remainding power
        elif load_half_hourly > generation_half_hourly:

            energy_source.iloc[index, 2] = int(generation_half_hourly)

            required_storage_energy_kwh = (load_half_hourly - generation_half_hourly) * 0.5 / STORAGE_DISCHARGE_EFFICIENCY # Add to cumulative energy storage total

            # If we can use the stored energy, use that
            if stored_energy_kwh >= required_storage_energy_kwh:
                stored_energy_kwh -= required_storage_energy_kwh

                energy_source.iloc[index, 3] = int(required_storage_energy_kwh * 2)
                # Update the peak energy storage power if this is a new maximum
                if (load_half_hourly - generation_half_hourly) > peak_storage_power_kw:
                    peak_storage_power_kw = load_half_hourly - generation_half_hourly

            # If there is some (but not enough) energy in the storage, use the rest of that. Then use the grid
            elif stored_energy_kwh < required_storage_energy_kwh and stored_energy_kwh > 0:
                grid.iloc[index, 1] = int(required_storage_energy_kwh - stored_energy_kwh)
                grid.iloc[index, 2] = int(2 * (required_storage_energy_kwh - stored_energy_kwh))

                energy_source.iloc[index, 3] = int(2 * stored_energy_kwh)
                energy_source.iloc[index, 4] = int(2 * (required_storage_energy_kwh - stored_energy_kwh))

                stored_energy_kwh = 0
            # Otherwise there is no storage left. Use the grid for full supply
            else:
                grid.iloc[index, 1] = int(required_storage_energy_kwh)
                grid.iloc[index, 2] = int(2 * required_storage_energy_kwh)

                energy_source.iloc[index, 4] = int(2 * required_storage_energy_kwh)

            below_counter += 1
        elif load_half_hourly == generation_half_hourly:
            # Do nothing when the load exactly matches generation (no energy storage release/recharge)
            energy_source.iloc[index, 2] = int(generation_half_hourly)
            pass
       
        storage_time_series.iloc[index, 1] = int(stored_energy_kwh)
        storage_time_series.iloc[index, 2] = int(2 * (stored_energy_kwh - stored_energy_prev_kwh))
        stored_energy_prev_kwh = stored_energy_kwh
        
        generation_index += 2

    energy_source_sums = energy_source.iloc[:, 2:].sum().to_dict()

    print("Energy storage size: {:.2f} KWh".format(STORAGE_CAPACITY_KWH))
    print("Peak energy power: {:.2f} KW".format(peak_storage_power_kw))
    print("Started analysis with {:.2f} Kwh energy stored".format(STORAGE_CAPACITY_KWH))
    print("Ended analysis with {:.2f} Kwh energy stored".format(stored_energy_kwh))    
    print("Generation above load for: {:.2f}%".format(100 * above_counter / (above_counter + below_counter)))
    print("Generation below load for: {:.2f}%".format(100 * below_counter / (above_counter + below_counter)))

    # If there is more energy available than what was started year with, it is sustainable
    if (stored_energy_kwh >= STORAGE_CAPACITY_KWH):
        print('\033[92m' + 'Sustainable solution!!!!!!' + '\033[0m')
    else:
        print("Unsustainable solution. This is difference of: {:.2f} Kwh".format(stored_energy_kwh - STORAGE_CAPACITY_KWH))

    # fig, ax = plt.subplots(figsize=(8, 6))
    # matched_gen_load.plot(0, 2, ax=ax, label='Data')
    # ax.axhline(y=0, color='gray', linestyle='--', label='Generation = Load')


    fig, ax = plt.subplots(figsize=(8, 6))
    grid.plot(0, 2, ax=ax, label='Grid usage (KW)')
    grid.plot(0, 4, ax=ax, label='Grid supply (KW)')
    ax.set_title('Grid Usage and Supply (KW)')
    ax.legend()

    fig, ax = plt.subplots(figsize=(8, 6))
    storage_time_series.plot(0, 1, ax=ax, label='Stored Energy (KWH)')
    storage_time_series.plot(0, 2, ax=ax, label='Energy Storage power (KW)')
    ax.set_title('Energy storage')
    ax.legend()

    print("------------- Grid Statistics --------------")
    print("Required Grid Energy (KWH): {:.2f}".format(np.sum(grid.iloc[:, 1])))
    print("Supplied Grid Energy (KWH): {:.2f}".format(np.sum(grid.iloc[:, 3])))

    print("-------- Energy Source Statistics ----------")
    total_load = load.iloc[:, 1].sum()
    print("Renewable (KW): {:.2f}%".format(100 * energy_source_sums['Renewable Generation (KW)'] / total_load))
    print("Storage (KW): {:.2f}%".format(100 * energy_source_sums['Storage (KW)'] / total_load))
    print("Grid (KW): {:.2f}%".format(100 * energy_source_sums['Grid (KW)'] / total_load))

    fig, ax = plt.subplots()
    ax.pie(energy_source_sums.values(), labels=energy_source_sums.keys())

    write_output(storage_time_series, STORAGE_OUTPUT_FILE)
    write_output(grid, GRID_OUTPUT_FILE)