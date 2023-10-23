# ENEL 667 Project Modelling
# Installation
Install requirements: `pip install -r requirements.txt`
# Calculate load, generation and storage requirements
Run `python main.py`
# Overview
### `FestivalPower.py`
Class for a calculating power consumption of a Music Festival.
### `generation_modelling.py`
Script to process wind data, average it, and calculation generation from the wind based on the Turbine power curve chosen. Takes as parameters: 
- Wind data
- Turbine Power Curve
- Number of Turbines

### `load_modelling.py`
Script to model and combine the electrical loads of Cardrona ski field, Cardrona Valley residential area, and Rhythm and Alps music festival

### `main.py`
Main routine to calculate all of load, generation, and grid usage

### `storage_modelling.py`
Script to calculate energy storage and grid usage. Can configure storage size to be 0 (full grid usage), or greater than 0 (combination of storage and grid usage).