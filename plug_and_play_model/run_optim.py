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

building = "ac_sanierterzustand" 
size = "dez" 
year = "ref"


devices_to_use = ["HP","AC", "PV", "BAT", "STC"] # Feasible devices

param, devs, dem, result_dict = load_params.load_params(building, size, year, devices_to_use)

param["observation_time"] = 10
devs ["PV"]["life_time"] = 5
param["enable_feed_in_el"] = True
param["revenue_feed_in_el"] = 0.01


result_dict = optim_model.run_optim(devs, param, dem, result_dict)

result_dict_name = "results/" + building +".json"

with open(result_dict_name, 'w') as json_file:
    json.dump(result_dict, json_file, indent=4)








#TODO: Nu au cum rezolva, dar se pare că EHDO ar da mai degrabă model infeasbile decât să folosească HP doar pentru cooling (e ceva la ordindea de priorități)

#TODO: Wenn enable_feed_in_el = False, dann ist manchmal infeasible, weil die ganze Strom kann nicht weggeworfen werden. Die model funktioniert aber wenn revenue_feed_in_el = 0.00 ist (also preismaßig egal).





















# Run post-processing
#post_processing.run(dir_results)
#post_processing.run(os.path.join(os.path.abspath(os.getcwd()), "Results", "test"))

    