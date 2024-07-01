import load_params
import optim_model
import os
import json
import numpy as np
import copy



"""
INFO:
    - Prețurile din param.json vin din         Energiepreise, pentru anul 2040
    - Co2       din param.json vin din THG_emissionsfaktoren, pentru anul 2040
"""

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


#TODO: ❗ Ceva nu e bine la calulcatul prețurilor. E mult mai mic decât cap * spez_price. Ceva e greșit la ann_factor, și la new_method = False. U
    # - [ ] Rulează o dată și în EHDO Web și vezi cam ce prețuri ai 
    # - [ ] Calculează costurile mai exact la Anlagen, luând din Quelle ce preț ar avea la capacitatea de acolo.
    # - [ ] Ce este total annual costs și ce e total annualized costs?
        # - Deci care contează dintre ăstea?
        # - Costurile nu au sens, nici nu se ia taxa de co2 în calcul

#TODO: Vezi technikkatalof Stromdirectheizung și Wärmenetze și haustaation fernwärme
    # - [ ] Pune după ăstea și în Diagrame
    # - [ ] Vezi pentru fiecare building dacă are Fernwärme și ce tip de Fernwärme (e verde sau din Kohl)
    # - [ ] Trebe să pui după și la calcualte costs un prChange pentru heat

#TODO: Caută alt interest_rate
#TODO: Caută valori pentru co2_feed_in

# ---------------------------------------------------------------

devices_to_use = ["HP", "BOI", "EB", "CHP", "BCHP", "PV", "STC", "BAT", "TES"] # Feasible devices


# -------------- First run

param, devs, dem, result_dict = load_params.load_params(building, size, devices_to_use)

# -------------- Parameters

param["observation_time"] = 10
param["roof_area"] = 100

# -------------- First Results

result_dict = optim_model.run_optim(devs, param, dem, result_dict)

""" # -------------- Second run (with Minimum Capacities)

min_cap = {
    "CHP":2.5,
    "HP":3.5, 
    "EB":4,
    "BAT": 4,
    "BBOI":12,
    }

min_area = {
    "PV":20,
    "STC":15}

min_vol = {
    "TES":5}

devices = list(result_dict["devices"].keys())
for device in devices:
    try:
        if device in ["PV", "STC"]:
            if result_dict["devices"][device]["area"] < min_area[device]:
                devices_to_use.remove(device)
        elif device in ["TES"]:
            if result_dict["devices"][device]["vol"] < min_vol[device]:
                devices_to_use.remove(device)
        elif result_dict["devices"][device]["cap"] < min_cap[device]:
            devices_to_use.remove(device)
    except:
        pass

param, devs, dem, result_dict = load_params.load_params(building, size, devices_to_use)
result_dict = optim_model.run_optim(devs, param, dem, result_dict)
"""

# -------------- Save results

# -------------- Update costs


new_specific_prices= { # Source: Technikkatalog 2309
    "dez": {
        "HP": { # L-W  WP
            "cap": [5,10,20,30,40,50,60,80,110],
            "price": [2000, 1819,1575,1545, 1449, 1365, 1303, 1255, 1182] 
        },
        "BOI": {
            "cap": [5,10,20,30,40,50,60,80,110],
            "price": [715, 358, 248, 166, 163]
        },
        "STC": {
            "cap": [4.2,10,20,140], # Capacity nu area
            "price": [950,848,774,600]
        },
        "PV":{
            "cap": [4,10,20],
            "price": [1800,1300, 1020]
        },
    },
    "zent":
    {
        "HP": { # Großwärmepumpe, Abwärme
            "cap": [300,1500, 5000, 20000],
            "price": [1708,939,800,501] 
        },
        "BOI":
        {
            "cap": [500,10000],
            "price": [120,98] 
        },
        "STC": {
            "cap": [350,700,1400,3500,7000,10500],
            "price": [447,423,402,375,354,345]
        },


    }
}



# for device in result_dict["devices"]:
#     if device in new_specific_prices[size]: # Dez or Zent
#         cap = result_dict["devices"][device]["cap"]
#         index_nearest_price = np.abs(np.array(new_specific_prices[size][device]["cap"]) - cap).argmin()

#         index_1 = index_nearest_price - 1 if index_nearest_price > 0 else 0 
#         index_2 = index_nearest_price + 1 if index_nearest_price < len(new_specific_prices[size][device]["cap"]) else len(new_specific_prices[size][device]["cap"])

#         price = np.interp(cap, [new_specific_prices[size][device]["cap"][index_1], new_specific_prices[size][device]["cap"][index_2]], [new_specific_prices[size][device]["price"][index_1], new_specific_prices[size][device]["price"][index_2]])

#         cost = round(price * cap,2)
#         result_dict["devices"][device]["cost"] = cost

# 16668
# 1166

result_dict_name = "results/" + building +".json"
with open(result_dict_name, 'w') as json_file:
    json.dump(result_dict, json_file, indent=4)


