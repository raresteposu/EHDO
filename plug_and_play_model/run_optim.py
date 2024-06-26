# -*- coding: utf-8 -*-
"""

INFO:
    - param[enable_feed_in] muss True sein, sonst kann die zusätzliche Energie nicht weggeworfen sein.

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

building = "ac_sanierterzustand" 
size = "dez" 

#TODO: De ce plm nu mai merge fără BAT sau TES?
    # Nu cred că fără ele nu ajunge la CO2 = 0, e sigur alt motiv

#TODO: De ce plm nu funcționează fără PV și STC ?

devices_to_use = ["HP", "BOI", "EB", "GHP", "PV", "STC", "BAT", "TES"] # Feasible devices

param, devs, dem, result_dict = load_params.load_params(building, size, devices_to_use)

param["observation_time"] = 10

"""
INFO:
    - Prețurile din param.json vin din         Energiepreise, pentru anul 2040
    - Co2       din param.json vin din THG_emissionsfaktoren, pentru anul 2040
        - #TODO: În cazul ăla, la 2040 oricum logic că CO2 al electricității va fii 0, deci ce rol mai are calculul cu date din 2040? 
        - #TODO: Ce valori să iei pentru co2_feed_in

"""



result_dict = optim_model.run_optim(devs, param, dem, result_dict)

result_dict_name = "results/" + building +".json"

with open(result_dict_name, 'w') as json_file:
    json.dump(result_dict, json_file, indent=4)







    