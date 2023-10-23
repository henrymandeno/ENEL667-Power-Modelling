import pandas as pd
import numpy as np

# Define Power Constants
SPEAKER_POWER_W = 1000 # https://www.lowendtheoryclub.com/how-many-watts-is-the-tomorrowland-2/
TICKET_STAND_POWER_W = 500 # (10 LED lights, 5 computers)
STAGE_LIGHT_POWER_W = 60 # (https://www.musicplanet.co.nz/chauvet-intimispot-led-255-moving-head-60-watt-led-8414591.html?gclid=Cj0KCQjw0vWnBhC6ARIsAJpJM6dLRXSUy8KMZuQjHiFOVMF4U0MQxDjTiEoboP43Tp2qPATTHwi5BXcaAqO3EALw_wcB)
FOOD_STAND_POWER_W = 8000 # https://shrinkthatfootprint.com/what-size-generator-do-i-need-for-a-food-truck/#:~:text=A%20small%20food%20truck%20serving,produces%208%2C000%20watts%20or%20more.
DRINK_STAND_POWER_W = 5000 
TOILET_STAND_POWER_W = 10000 #https://www.viessmann.co.uk/en/heating-advice/boilers/which-appliances-use-most-energy-at-home.html#:~:text=Electric%20showers%20are%20sized%20in,of%20energy%20in%20six%20minutes.
CAMPERVAN_OUTLET_POWER_W = 3500 #https://blog.ecoflow.com/uk/motorhome-generator-size-guide/#:~:text=A%203%2C500%2Dwatt%20generator%20is,lights%20at%20the%20same%20time.
LIGHT_POWER_W = 400 # https://commercialledlights.com/blog/outdoor-lighting/led-flood-light-buyers-guide/#:~:text=LED%20flood%20lights%20come%20in,which%20also%20correlates%20to%20heat.

class Stage:
    def __init__(self, name, speakers, lights, schedule):
        self.name = name
        self.speakers = speakers
        self.lights = lights
        self.schedule = schedule

    def calculate_stage_power(self):
        stage_power = self.speakers * SPEAKER_POWER_W + self.lights * STAGE_LIGHT_POWER_W

        stage_power_times = pd.DataFrame(stage_power * self.schedule.iloc[:, 1])

        stage_power_times.insert(0, 'Date Time', self.schedule.iloc[:, 0])

        return stage_power_times
    

class Festival:
    def __init__(self, name, ticketing_stands, food_stands, drink_stands, toilet_stands, campervan_outlets, lights):
        self.name = name
        self.ticketing_stands = ticketing_stands
        self.food_stands = food_stands
        self.drink_stands = drink_stands
        self.toilet_stands = toilet_stands
        self.campervan_outlets = campervan_outlets
        self.lights = lights
        self.stages = []
        self.total_power = pd.DataFrame(np.zeros((192, 2)))

    def add_stage(self, stage):
        self.stages.append(stage)

    def calculate_festival_power(self):
        total_power = pd.DataFrame(np.zeros((192, 2)))
        total_power.iloc[:, 0] = self.stages[0].schedule.iloc[:, 0]

        # ------------------- Stages ---------------------
        for i in range(len(self.stages)):
            stage_power = self.stages[i].calculate_stage_power().iloc[:, 1]
            total_power.iloc[:, 1] += stage_power
        

        # --------------- Constant power -----------------
        total_power.iloc[:, 1] += self.ticketing_stands * TICKET_STAND_POWER_W
        total_power.iloc[:, 1] += self.campervan_outlets * CAMPERVAN_OUTLET_POWER_W
        total_power.iloc[:, 1] += self.food_stands * FOOD_STAND_POWER_W
        total_power.iloc[:, 1] += self.drink_stands * DRINK_STAND_POWER_W
        total_power.iloc[:, 1] += self.toilet_stands * TOILET_STAND_POWER_W
        total_power.iloc[:, 1] += self.lights * LIGHT_POWER_W

        # total_power.plot(0, 1, legend=None)
        # plt.ylabel("Power (W)")
        # plt.show()

        # Convert to kW
        total_power.iloc[:, 1] = total_power.iloc[:, 1] / 1000

        self.total_power = total_power
        return total_power

    def calculate_peak_festival_power(self):
        return np.max(self.total_power.iloc[:, 1])