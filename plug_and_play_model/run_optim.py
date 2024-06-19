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
optim_focus = [0, 1]

building = "ref" 
size = "ref" 
year = "ref"


devices_to_use = ["HP","BBOI","BOI","CHP", "PV", "BAT", "TS", "ELYZ", "AC", "BHCP", "STC"] # Feasible devices

param, devs, dem, result_dict = load_params.load_params(building, size, year, devices_to_use)

param['optim_focus'] = 1

#TODO: Când am dat focus = 1, sau băgat și BOI și chp dar care arată generated = 0, deși au cap și cost mare

result_dict = optim_model.run_optim(devs, param, dem, result_dict)

result_dict_name = "results/" + building + "_focus-" + str(param["optim_focus"]) + ".json"

with open(result_dict_name, 'w') as json_file:
    json.dump(result_dict, json_file, indent=4)

























# Run post-processing
#post_processing.run(dir_results)
#post_processing.run(os.path.join(os.path.abspath(os.getcwd()), "Results", "test"))

    