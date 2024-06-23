import copy
import json
import numpy as np
import math
import clustering_medoid as clustering
import time
import os
import csv
import solar_modeling
from optim_model import run_optim  # Ensure this import is at the top of your fileE

def update_dict_recursively(dict1, dict2):
    """
    Recursively updates dict1 with values from dict2.
    """
    for key, value in dict2.items():
        if isinstance(value, dict) and key in dict1 and isinstance(dict1[key], dict):
            update_dict_recursively(dict1[key], value)
        else:
            dict1[key] = value
    return dict1

def load_params(building, size, year, devices_to_use,obs_time):

    result_dict = {}
    param = {}  # general parameters

    param_uncl = {}  # unclustered time series for weather data

    path_input_data = ".\\plug_and_play_model\\input_data\\"

    current_working_directory = os.getcwd()
    # print(f"Current working directory: {current_working_directory}")

    ################################################################
    #%%  GENERAL PARAMETERS

    param["c_w"] = 4.18  # kJ/(kgK)
    param["rho_w"] = 1000  # kg/m3

    #################################################################
    #%%  LOAD WEATHER DATA

    header = {}
    with open(os.path.join(path_input_data, "DEU_Dusseldorf.104000_IWEC.epw"), newline="", errors="ignore") as csvfile:
        csvreader = csv.reader(csvfile, delimiter=",", quotechar='"')
        for row in csvreader:
            if row[0].isdigit():
                break
            else:
                header[row[0]]=row[1:]

    timezone = float(header["LOCATION"][7])
    altitude = float(header["LOCATION"][8])

    file = open(os.path.join(path_input_data, "DEU_Dusseldorf.104000_IWEC.epw"), "rb")
    T_air, GHI, DHI, wind_speed = np.loadtxt(file, delimiter=",", skiprows=8, usecols=[6,13,15,21], unpack=True)

    param_uncl["T_air"] = T_air
    param_uncl["GHI"] = GHI
    param_uncl["DHI"] = DHI
    param_uncl["wind_speed"] = wind_speed

    ################################################################
    #%%  LOAD DEMANDS

    dem_uncl = {}

    dem_uncl["heat"] = np.loadtxt(os.path.join(path_input_data, "demand_heating_"+building+".txt"))
    dem_uncl["power"] = np.loadtxt(os.path.join(path_input_data, "demand_electricity_"+building+".txt"))

    
    try:
        dem_uncl["cool"] = np.loadtxt(os.path.join(path_input_data, "demand_cooling_"+building+".txt"))
    except:
        dem_uncl["cool"] = np.zeros(8760)
    try:
        dem_uncl["hydrogen"] = np.loadtxt(os.path.join(path_input_data, "demand_hydrogen_"+building+".txt"))
    except:
        dem_uncl["hydrogen"] = np.zeros(8760)

    for k in ["heat", "cool", "power", "hydrogen"]:
        param["peak_"+k] = np.max(dem_uncl[k])


    ################################################################
    #%%  DESIGN DAY CLUSTERING

    param["n_clusters"] = 8  # Number of design days

    # Collect the time series to be clustered
    time_series = [dem_uncl["heat"], dem_uncl["cool"], dem_uncl["power"], dem_uncl["hydrogen"], param_uncl["T_air"], param_uncl["GHI"], param_uncl["DHI"], param_uncl["wind_speed"]]
    # Only building demands and weather data are clustered using k-medoids algorithm; secondary time series are clustered manually according to k-medoids result
    inputs_clustering = np.array(time_series)
    # Execute k-medoids algorithm
    start = time.time()
    (clustered_series, nc, z) = clustering.cluster(inputs_clustering,
                                     param["n_clusters"],
                                     norm = 2,
                                     mip_gap = 0.02,
                                     )
    # print("Design day clustering finished. (" + str(time.time()-start) + ")\n")

    # Observation time

    param["observation_time"] = obs_time

    # Save clustered time series

    dem = {}
    dem["heat"] = clustered_series[0]
    dem["cool"] = clustered_series[1]
    dem["power"] = clustered_series[2]
    dem["hydrogen"] = clustered_series[3]
    param["T_air"] = clustered_series[4]
    param["GHI"] = clustered_series[5]
    param["DHI"] = clustered_series[6]
    param["wind_speed"] = clustered_series[7]

    # Save number of design days and design-day matrix
    param["day_weights"] = nc
    param["day_matrix"] = z

    # Get sigma-function: for each day of the year, find the corresponding design day
    # Get list of days which are used as design days
    typedays = np.zeros(param["n_clusters"], dtype = np.int32)
    n = 0
    for d in range(365):
        if any(z[d]):
            typedays[n] = d
            n += 1
    # Assign each day of the year to its design day
    sigma = np.zeros(365, dtype = np.int32)
    for day in range(len(sigma)):
        d = np.where(z[:,day] == 1 )[0][0]
        sigma[day] = np.where(typedays == d)[0][0]
    param["sigma"] = sigma

    # Cluster secondary time series
    #for k in ["T_air", "GHI", "wind_speed"]:
    #    series_clustered = np.zeros((param["n_clusters"], 24))
    #    for d in range(param["n_clusters"]):
    #        for t in range(24):
    #            series_clustered[d][t] = param_uncl[k][24*typedays[d]+t]
        # Replace original time series with the clustered one
    #    param[k] = series_clustered

    ################################################################
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    #%%  LOAD TECHNICAL PARAMETERS

    devs = {}
    

    data_devs_reference_path = ".\\plug_and_play_model\\input_data\\devs_ref.json"
    with open(data_devs_reference_path, 'r') as file:
        data_devs_reference = json.load(file)
    
    devs = data_devs_reference

    devs_path = ".\\plug_and_play_model\\input_data\\devs_"+size+".json"
    with open(devs_path, 'r') as file:
        data_devs = json.load(file)

    # Give an error if data_devs contains a key that is not in devs

    for key in data_devs.keys():
        if key not in devs.keys():
            raise ValueError(f"Key {key} in from the devs_{size}.json file was not found in the devs_ref.json.")

    devs = update_dict_recursively(devs, data_devs)

    for device in devs.keys():
        if device not in devices_to_use:
            devs[device]["feasible"] = False
        else:
            devs[device]["feasible"] = True

    
    devs["PV"]["norm_power"] = solar_modeling.pv_system(direct_tilted_irrad = param["GHI"] - param["DHI"],
                                                 diffuse_tilted_irrad = param["DHI"],
                                                 theta = 0,
                                                 T_air = param["T_air"],
                                                 wind_speed = param["wind_speed"]
                                                 )/1e3  # in kW/kWp

    devs["WT"]["norm_power"] = calc_WT_power(devs, param) # relative power between 0 and 1

    devs["STC"]["specific_heat"] = solar_modeling.collector_system(direct_tilted_irrad = param["GHI"] - param["DHI"],
                                                              diffuse_tilted_irrad = param["DHI"],
                                                              theta = 0,
                                                              T_air = param["T_air"]
                                                              )/1e3


    eta_carnot = devs["HP"]["eta_carnot"]
    supply_temp = devs["HP"]["supply_temp"]

    COP = np.zeros((param["n_clusters"], 24))
    for d in range(param["n_clusters"]):
        for t in range(24):
            COP[d][t] = eta_carnot * (supply_temp+273.15)/(supply_temp-param["T_air"][d][t])
    
    devs["HP"]["COP"] = COP
        

    deltaT = 40
    devs["TES"]["inv_var"] = 500 / (param["rho_w"] * param["c_w"] * deltaT / 3600) # EUR/kWh
    devs["TES"]["min_cap"] = 0 * param["rho_w"] * param["c_w"] * deltaT / 3600 # kWh
    devs["TES"]["max_cap"] = 100000 * param["rho_w"] * param["c_w"] * deltaT / 3600 # kWh
    devs["TES"]["delta_T"] = deltaT # K

    devs["CTES"]["inv_var"] = 500 / (param["rho_w"] * param["c_w"] * deltaT / 3600) # EUR/kWh
    devs["CTES"]["min_cap"] = 0 * param["rho_w"] * param["c_w"] * deltaT / 3600 # kWh
    devs["CTES"]["max_cap"] = 100000 * param["rho_w"] * param["c_w"] * deltaT / 3600 # kWh
    devs["CTES"]["delta_T"] = deltaT # K



    ################################################################
    #%%  LOAD MODEL PARAMETERS


    param_path = ".\\plug_and_play_model\\input_data\\param_"+year+".json"
    with open(param_path, 'r') as file:
        data_param = json.load(file)

    param = update_dict_recursively(param, data_param)

    ################################################################
    #%%  INITIALIZE CALCULATION

    # Calculate annual investments
    # devs, param = calc_annual_investment(devs, param)

    # Calculate reference scenario
    # result_dict = calc_reference(devs, dem, param, dem_uncl, result_dict)

    # Calculate values for post-processing
    result_dict = calc_monthly_dem(dem_uncl, param_uncl, result_dict)

    return param, devs, dem, result_dict

#%% SUB-FUNCTIONS ##################################################

import optim_model as optim_model


def calc_monthly_dem(dem_uncl, param_uncl, result_dict):

    month_tuple = ("Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec")
    days_sum = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334, 365]

    monthly_dem = {}
    year_peak = {}
    year_sum = {}
    for m in ["heat", "cool", "power", "hydrogen"]:
        monthly_dem[m] = {}
        year_peak[m] = int(np.max(dem_uncl[m]))
        year_sum[m] = int(np.sum(dem_uncl[m]))
        for month in range(12):
            monthly_dem[m][month_tuple[month]] = int(sum(dem_uncl[m][t] for t in range(days_sum[month]*24, days_sum[month+1]*24)))
    result_dict["demands"] = {}

    result_dict["demands"]["sum"] = year_sum
    result_dict["demands"]["peak"] = year_peak
    result_dict["demands"]["monthly"] = monthly_dem

    return result_dict


def calc_WT_power(devs, param):
    """
    According to data sheet of wind turbine Enercon E40.
    """

    power_curve = {0:  (0.0,    0.00),
                   1:  (2.4,    0.00),
                   2:  (2.5,    1.14),
                   3:  (3.0,    4.37),
                   4:  (3.5,   10.64),
                   5:  (4.0,   18.87),
                   6:  (4.5,   29.77),
                   7:  (5.0,   40.39),
                   8:  (5.5,   52.85),
                   9:  (6.0,   69.36),
                   10: (6.5,   88.02),
                   11: (7,    112.19),
                   12: (7.5,  134.67),
                   13: (8,    165.38),
                   14: (8.5,  197.08),
                   15: (9,    236.89),
                   16: (9.5,  279.46),
                   17: (10,   328.00),
                   18: (10.5, 362.93),
                   19: (11,   396.64),
                   20: (11.5, 435.27),
                   21: (12,   465.15),
                   22: (12.5, 483.63),
                   23: (13,   495.95),
                   24: (14,   500.00),
                   25: (25,   500.00),
                   26: (25.1,   0.00),
                   27: (1000,   0.00),
                   }

    wind_speed_corr = param["wind_speed"]*(devs["WT"]["hub_h"]/devs["WT"]["ref_h"]) ** devs["WT"]["h_coeff"]  # kW

    WT_power = np.zeros(np.shape(wind_speed_corr))
    for d in range(param["n_clusters"]):
        for t in range(24):
            WT_power[d][t] = get_turbine_power(wind_speed_corr[d][t], power_curve)

    WT_power_norm = WT_power / 500  # power_curve with 500 kW as maximum output

    return WT_power_norm


def get_turbine_power(wind_speed, power_curve):
    if wind_speed <= 0:
        return 0
    if wind_speed > power_curve[len(power_curve)-1][0]:
        print("Error: Wind speed is " + str(wind_speed) + " m/s and exceeds wind power curve table.")
        return 0

    # Linear interpolation:
    for k in range(len(power_curve)):
        if power_curve[k][0] > wind_speed:
           power = (power_curve[k][1]-power_curve[k-1][1])/(power_curve[k][0]-power_curve[k-1][0]) * (wind_speed-power_curve[k-1][0]) + power_curve[k-1][1]
           break
    return power
