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


buildings = ["reference",
             "ac_istzustand", 
             "ac_sanierterzustand", 
             "pmh_istzustand",
             "pmh_sanierterzustand",
             "hnbk_istzustand",
             "hnbk_sanierterzustand",
             "sk_istzustand",
             "sk_sanierterzustand"]
size = ["ref", "dez", "zent"]
years = ["ref", "2024", "2030", "2040", "2045"]

building = "ac_istzustand" 
size = "dez" 
year = "ref"


devices_to_use = ["HP","BOI", "CHP","BCHP", "AC", "PV", "STC", "EB", "BBOI", "BAT"] # Feasible devices

obs_time = 10

param, devs, dem, result_dict = load_params.load_params(building, size, year, devices_to_use, obs_time)


result_dict = optim_model.run_optim(devs, param, dem, result_dict)

result_dict_name = "results/" + building + "_" + str(obs_time) +".json"

with open(result_dict_name, 'w') as json_file:
    json.dump(result_dict, json_file, indent=4)


#TODO: La life_time = 6, cost-urile sunt mult mai mici, deși trebe să fie mai mari.

#TODO: Pune limits la grid. Și la vândut și la luat.


#TODO: Should we also use heatpumps for cooling?





















# Run post-processing
#post_processing.run(dir_results)
#post_processing.run(os.path.join(os.path.abspath(os.getcwd()), "Results", "test"))

    