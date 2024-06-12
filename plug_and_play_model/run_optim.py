# -*- coding: utf-8 -*-
"""

EHDO - ENERGY HUB DESIGN OPTIMIZATION Tool

Developed by:   E.ON Energy Research Center, 
                Institute for Energy Efficient Buildings and Indoor Climate, 
                RWTH Aachen University, 
                Germany
               
Contact:        Marco Wirtz 
                marco.wirtz@eonerc.rwth-aachen.de

"""


import load_params
import optim_model
#import post_processing
import os
import json
import numpy as np
import copy

# -----------------------------------------------------------------------------

# My plan was to run the algorithm once, get the results, and then check if the capcacity results were bigger then the minimal capacity allowed for each device. If not, deactivate all devices with capacity lower than the minimum allowed capacity and run the algorithm again.

# I didn't manage to make it work. I don't understand the codebase and it is poorly documentated. It seems that load_params calculates something as well, as i get the same result_dict with the optim_model and without it.
   
# -----------------------------------------------------------------------------

# _cap = capacity of the unit in kW
# _total = total heat/electricity generated by the unit in kWh
# _costs / _om / tac = total costs of the unit in €
# co2 = total CO2 emissions in kg

# monthy_dem = monthly demand in kWh
# peak = peak demand in kW
# yearly_dem = sum of all monthy demands = yearly demand in kWh

# -----------------------------------------------------------------------------

min_allowed_capacities = {
    "hp_cap": 3000,  
    "boi_cap": 5, 
}

def run_optimization(param, devs, dem, result_dict):
    # Run optimization with updated devices
    result_dict = optim_model.run_optim(devs, param, dem, result_dict)
    return result_dict

def check_and_deactivate(param, devs, result_dict, min_allowed_capacities):
    changes_made = False
    modified_devs = {}
    for device, min_capacity in min_allowed_capacities.items():
        if result_dict.get(device, 0) < min_capacity:
            device_key = device.split('_')[0]
            device_key = device_key.upper()
            if device_key in devs:

                devs[device_key]['feasible'] = False
                devs[device_key]['max_cap'] = 0

                modified_devs[device_key] = {
                    'feasible': devs[device_key]['feasible'],
                    'max_cap': devs[device_key]['max_cap']
                }

                changes_made = True
    return changes_made, modified_devs

# Inital run 

buildings = ["reference",
             "ac_istzustand", 
             "ac_sanierterzustand", 
             "pmh_istzustand",
             "pmh_sanierterzustand",
             "hnbk_istzustand",
             "hnbk_sanierterzustand",
             "sk_istzustand",
             "sk_sanierterzustand"]
size = ["reference", "dez", "zent"]
years = ["reference", "2024", "2030", "2040", "2045"]


building = "reference"
size = "reference"
year = "reference"
devices_to_use = ["HP", "BOI", "CHP", "PV", "BAT"] # Feasible devices

param, devs, dem, result_dict = load_params.load_params(building, size, year, devices_to_use)

result_dict = run_optimization(param, devs, dem, result_dict)

with open('result_dict.json', 'w') as json_file:
    json.dump(result_dict, json_file, indent=4)


''' Check and rerun

changes_made, modified_devs = check_and_deactivate(param, devs, result_dict, min_allowed_capacities)

if changes_made:
    print("Modified devices:", modified_devs)

    result_dict = run_optimization(param, devs, dem, result_dict)

'''

























# Run post-processing
#post_processing.run(dir_results)
#post_processing.run(os.path.join(os.path.abspath(os.getcwd()), "Results", "test"))

    