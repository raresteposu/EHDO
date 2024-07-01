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

# ----------------------------------------

#TODO: ❗ Ceva nu e bine la calculatul costului. Nu este c_inv * cap, ci e mult mult mai mic.
    # - Înțelege chestiile ălea de economie, mai ales că trebe să calculezi din nou cu prețurile bune

#TODO: Results.xlsx e corupt, ial de pe git

#TODO: Caută valori pentru co2_feed_in
    # - Nu ar fii logiv să scaleze cu cât de verde este producția?

# ----------------------------------------

buildings = ["reference",
             "ac_istzustand", 
             "ac_sanierterzustand", 
             "pmh_istzustand",
             "pmh_sanierterzustand",
             "hnbk_istzustand",
             "hnbk_sanierterzustand",
             "sk_istzustand",
             "sk_sanierterzustand",
             "quart_istzustand",
             "quart_sanierterzustand"]


size = ["ref", "dez", "zent"]

building = "ac_sanierterzustand" # Choose building


# -------------- User input

building = "ac_sanierterzustand" 

devices_to_use = ["HP", "BOI", "EB", "CHP", "BCHP", "PV", "STC", "BAT", "TES"] # Feasible devices


# -------------- Building specific parameters

if building[:2] == "ac": roof_area = 152; size = "dez"
if building[:3] == "pmh": roof_area = 123; size = "dez"; devices_to_use.remove("BCHP").remove("CHP")
if building[:4] == "hnbk": roof_area = 1600; size = "dez"
if building[:2] == "sk": roof_area = 0; size = "dez"
if building[:4] == "quart": roof_area = 100000; size = "zent"



# -------------- Load parameters (First run)

param, devs, dem, result_dict = load_params.load_params(building, size, devices_to_use)

# -------------- Parameters

param["observation_time"] = 10
param["roof_area"] = roof_area

if building[:2] == "ac": param["enable_supply_heat"] = True
if building[:3] == "pmh": param["enable_supply_heat"] = True 
if building[:4] == "hnbk": param["enable_supply_heat"] = False
if building[:2] == "sk": param["enable_supply_heat"] = False

if size == "zent":
    param["price_supply_el"] = 67
    param["price_supply_gas"] = 15
    param["enable_supply_heat"] = False
    param["enable_supply_el"] = False
    param["enable_supply_gas"] = False
    param["feed_in_el_limit"] = 1000000000

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

devices = list(result_dict["Devices"].keys())
for device in devices:
    try:
        if device in ["PV", "STC"]:
            if result_dict["Devices"][device]["area"] < min_area[device]:
                devices_to_use.remove(device)
        elif device in ["TES"]:
            if result_dict["Devices"][device]["vol"] < min_vol[device]:
                devices_to_use.remove(device)
        elif result_dict["Devices"][device]["cap"] < min_cap[device]:
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


for device in result_dict["Devices"]:
    if device in new_specific_prices[size]: # Dez or Zent
        cap = result_dict["Devices"][device]["cap"]
        index_nearest_price = np.abs(np.array(new_specific_prices[size][device]["cap"]) - cap).argmin()

        index_1 = index_nearest_price - 1 if index_nearest_price > 0 else 0 
        index_2 = index_nearest_price + 1 if index_nearest_price < len(new_specific_prices[size][device]["cap"]) else len(new_specific_prices[size][device]["cap"])

        price = np.interp(cap, [new_specific_prices[size][device]["cap"][index_1], new_specific_prices[size][device]["cap"][index_2]], [new_specific_prices[size][device]["price"][index_1], new_specific_prices[size][device]["price"][index_2]])

        cost = round(price * cap,2)
        result_dict["Devices"][device]["cost"] = cost


# -------------- Save results

result_dict_name = "results/" + building +".json"
with open(result_dict_name, 'w') as json_file:
    json.dump(result_dict, json_file, indent=4)


