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

import math
import gurobipy as gp
import numpy as np
import time
import os
#from optim_app.help_functions import create_excel_file


def run_optim(devs, param, dem, result_dict):

    #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Load model parameters
    start_time = time.time()

    days = range(param["n_clusters"])
    time_steps = range(24)
    year = range(365)

    # Get sigma function which assigns every day of the year to a design day
    sigma = param["sigma"]

    # Create set for devices
    all_devs = ["PV", "WT", "STC", "WAT",
                "HP", "EB", "CC", "AC", 
                "CHP", "BOI", "GHP",
                "BCHP", "BBOI", "WCHP", "WBOI",
                "ELYZ", "FC", "H2S", "SAB",                
                "TES", "CTES", "BAT", "GS",  
                ]
   
    #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Set up model and create variables

    # Create a new model
    model = gp.Model("Energy_hub_model")
    
    # Purchase decision binary variables (1 if device is installed, 0 otherwise)
    x = {}
    for device in all_devs:
        x[device] = model.addVar(vtype="B", name="x_" + str(device))
        
    # Device's capacity (i.e. rated power)
    cap = {}
    for device in all_devs:
        cap[device] = model.addVar(vtype="C", name="nominal_capacity_" + str(device))
        
    # Roof area used for PV and solar thermal collector installation
    area = {}
    for device in ["PV", "STC"]:
        area[device] = model.addVar(vtype = "C", name="roof_area_" + str(device))
        
    # Gas flow to/from devices
    gas = {}
    for device in ["CHP", "BOI", "GHP", "SAB", "from_grid", "to_grid"]:
        gas[device] = {}
        for d in days:
            gas[device][d] = {}
            for t in time_steps:
                gas[device][d][t] = model.addVar(vtype="C", name="gas_" + device + "_d" + str(d) + "_t" + str(t))
    
    # Electric power to/from devices
    power = {}
    for device in ["PV", "WT", "WAT", "HP", "EB", "CC", "CHP", "BCHP", "WCHP", "ELYZ", "FC", "from_grid", "to_grid"]:
        power[device] = {}
        for d in days:
            power[device][d] = {}
            for t in time_steps:
                power[device][d][t] = model.addVar(vtype="C", name="power_" + device + "_d" + str(d) + "_t" + str(t))
       
    # Heat to/from devices
    heat = {}
    for device in ["STC", "HP", "EB", "AC", "CHP", "BOI", "GHP", "BCHP", "BBOI", "WCHP", "WBOI", "FC"]:
        heat[device] = {}
        for d in days:
            heat[device][d] = {}
            for t in time_steps:
                heat[device][d][t] = model.addVar(vtype="C", name="heat_" + device + "_d" + str(d) + "_t" + str(t))
    
    # Cooling power to/from devices
    cool = {}
    for device in ["CC", "AC"]:
        cool[device] = {}
        for d in days:
            cool[device][d] = {}
            for t in time_steps:
                cool[device][d][t] = model.addVar(vtype="C", name="cool_" + device + "_d" + str(d) + "_t" + str(t))
                
    # Hydrogen to/from devices
    hydrogen = {}
    for device in ["ELYZ", "FC", "SAB", "import"]:
        hydrogen[device] = {}
        for d in days:
            hydrogen[device][d] = {}
            for t in time_steps:
                hydrogen[device][d][t] = model.addVar(vtype="C", name="hydrogen_" + device + "_d" + str(d) + "_t" + str(t))
                
    # Biomass to devices
    biom = {}
    for device in ["BCHP", "BBOI", "import"]:
        biom[device] = {}
        for d in days:
            biom[device][d] = {}
            for t in time_steps:
                biom[device][d][t] = model.addVar(vtype="C", name="biom_" + device + "_d" + str(d) + "_t" + str(t))
                
    # Waste to devices
    waste = {}
    for device in ["WCHP", "WBOI", "import"]:
        waste[device] = {}
        for d in days:
            waste[device][d] = {}
            for t in time_steps:
                waste[device][d][t] = model.addVar(vtype="C", name="waste_" + device + "_d" + str(d) + "_t" + str(t))

    # Storage variables
    ch = {}  # Energy flow to charge storage device
    soc = {} # State of charge
    for device in ["TES", "CTES", "BAT", "H2S", "GS"]:
        ch[device] = {}
        soc[device] = {}
        for d in days:
            ch[device][d] = {}
            for t in time_steps:
                # For charge variable: ch is positive if storage is charged, and negative if storage is discharged
                ch[device][d][t] = model.addVar(vtype="C", lb=-gp.GRB.INFINITY, name="ch_" + device + "_d" + str(d) + "_t" + str(t))
        for day in year:
            soc[device][day] = {}
            for t in time_steps:
                soc[device][day][t] = model.addVar(vtype="C", name="soc_" + device + "_d" + str(day) + "_t" + str(t))

    # Variables for annual device costs     
    
    inv = {}
    c_inv = {}
    c_om = {}
    c_total = {}
    c_dem = {}
    for device in all_devs:
        inv[device] = model.addVar(vtype = "C", name="investment_costs_" + device)
    for device in all_devs:
        c_inv[device] = model.addVar(vtype = "C", name="annual_investment_costs_" + device)
    for device in all_devs:
        c_om[device] = model.addVar(vtype = "C", name="om_costs_" + device)
    for device in all_devs:
        c_dem[device] = model.addVar(vtype = "C", name="demand_related_costs_" + device)
    for device in all_devs:
        c_total[device] = model.addVar(vtype = "C", name="total_annual_costs_" + device)   

    # Capacity of grid connections (gas and electricity)
    grid_limit_el  = model.addVar(vtype = "C", name="grid_limit_el")  
    grid_limit_gas = model.addVar(vtype = "C", name="grid_limit_gas")    
    
    # Total energy amounts taken from grid and fed into grid
    from_el_grid_total = model.addVar(vtype = "C", name="from_el_grid_total")
    to_el_grid_total   = model.addVar(vtype = "C", name="to_el_grid_total")
    
    from_gas_grid_total = model.addVar(vtype = "C", name="from_gas_grid_total")
    to_gas_grid_total   = model.addVar(vtype = "C", name="to_gas_grid_total")
    
    biom_import_total     = model.addVar(vtype = "C", name="biom_import_total")
    waste_import_total    = model.addVar(vtype = "C", name="waste_import_total")
    hydrogen_import_total = model.addVar(vtype = "C", name="hydrogen_import_total")
    
    # Total revenue for feed-in
    rev_feed_in_gas = model.addVar(vtype="C", name="rev_feed_in_gas")
    rev_feed_in_el  = model.addVar(vtype="C", name="rev_feed_in_el")

    # Electricity/gas/biomass costs
    supply_costs_el       = model.addVar(vtype = "C", name="supply_costs_el")    
    cap_costs_el          = model.addVar(vtype = "C", name="cap_costs_el")    
    supply_costs_gas      = model.addVar(vtype = "C", name="supply_costs_gas")    
    cap_costs_gas         = model.addVar(vtype = "C", name="cap_costs_gas")    
    supply_costs_biom     = model.addVar(vtype = "C", name="supply_costs_biomass")   
    supply_costs_waste    = model.addVar(vtype = "C", lb=-gp.GRB.INFINITY, name="supply_costs_waste")   
    supply_costs_hydrogen = model.addVar(vtype = "C", name="supply_costs_hydrogen")       
    
    #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Define the objectives
    obj = {}
    obj["tac"] = model.addVar(vtype="C", lb=-gp.GRB.INFINITY, name="total_annualized_costs")
    obj["co2"] = model.addVar(vtype="C", lb=-gp.GRB.INFINITY, name="total_CO2")

    # Update the model to integrate the new variables
    model.update()

    # Add constraints for total annualized costs
    model.addConstr(obj["tac"] == (
        sum(c_total[dev] for dev in all_devs) +  # annualized investments
        supply_costs_gas + cap_costs_gas +       # gas costs
        supply_costs_el + cap_costs_el -         # electricity costs
        rev_feed_in_el - rev_feed_in_gas +       # revenues
        supply_costs_biom +                      # biomass
        supply_costs_waste +                     # waste
        supply_costs_hydrogen +                  # hydrogen
        (from_gas_grid_total * param["co2_gas"] +
        biom_import_total * param["co2_biom"] +
        waste_import_total * param["co2_waste"]) * param["co2_tax"])  # CO2 tax
    )

    # Add constraints for total CO2 emissions
    model.addConstr(obj["co2"] == (
        from_el_grid_total * param["co2_el_grid"] +
        from_gas_grid_total * param["co2_gas"] +
        biom_import_total * param["co2_biom"] +
        waste_import_total * param["co2_waste"] +
        hydrogen_import_total * param["co2_hydrogen"] -
        to_el_grid_total * param["co2_el_feed_in"] -
        to_gas_grid_total * param["co2_gas_feed_in"]
    ))

    # Set the primary objective to minimize the total annualized costs
    model.setObjectiveN(obj["tac"], index=0, priority=1)

    # If the observation time is less than 16, set a secondary objective to minimize CO2 emissions
    # if param["observation_time"] < 16:
    #     model.setObjectiveN(obj["co2"], index=1, priority=2)
    # else:
    #     # Ensure CO2 emissions are below or equal to 0 if observation time is 16 or more
    #     model.addConstr(obj["co2"] <= 1e-6)

    model.addConstr(obj["co2"] <= 1e-6)
    # Optimize the model
    model.optimize()



    #%% Constraints


    for device in all_devs:
        if devs[device]["feasible"] == True:
            model.addConstr(x[device] == 1)
            if device not in ["PV", "STC"]:
                model.addConstr(cap[device] >= devs[device]["min_cap"])
                model.addConstr(cap[device] <= devs[device]["max_cap"])  
        else:
            model.addConstr(x[device] == 0)
            if device not in ["PV", "STC"]:
                model.addConstr(cap[device] == devs[device]["min_cap"])
            
      
    #%% CONTINUOUS SIZING OF DEVICES: minimum capacity <= capacity <= maximum capacity

    for d in days:
        for t in time_steps:
            for device in ["STC", "EB", "HP", "BOI", "GHP", "BBOI", "WBOI"]:
                model.addConstr(heat[device][d][t] <= cap[device])

            for device in ["CHP", "BCHP", "WCHP"]:
                model.addConstr(heat[device][d][t] <= cap[device])

            for device in ["PV", "WT", "WAT", "CHP", "BCHP", "WCHP", "ELYZ", "FC"]:
                model.addConstr(power[device][d][t] <= cap[device])

            for device in ["CC", "AC"]:
                model.addConstr(cool[device][d][t] <= cap[device])
                
            for device in ["SAB"]:
                model.addConstr(gas[device][d][t] <= cap[device])
                
            # Limitation of power from and to grid   
            for device in ["from_grid", "to_grid"]:
                model.addConstr(power[device][d][t] <= grid_limit_el)
                model.addConstr(gas[device][d][t]   <= grid_limit_gas)    

            # PV and STC: minimum area < used roof area <= maximum area
            for device in ["PV", "STC"]:            
                model.addConstr(area[device] >= x[device] * devs[device]["min_area"])
                model.addConstr(area[device] <= x[device] * devs[device]["max_area"])
            
            # Correlation between PV area and peak power; cap["PV"] is only needed for calculating investment costs
            model.addConstr(cap["PV"] == area["PV"] * devs["PV"]["G_stc"] * devs["PV"]["eta"])
            
            # Correlation between STC area and peak power; cap["STC"] is only needed for calculating investment costs
            model.addConstr(cap["STC"] == area["STC"] * devs["STC"]["G_stc"] * devs["STC"]["eta"])
            
                
        
    # state of charge < storage capacity
    for device in ["TES", "CTES", "BAT", "H2S", "GS"]:
        for day in year:
            for t in time_steps:    
                model.addConstr(soc[device][day][t] <= cap[device])

    #%% INPUT / OUTPUT CONSTRAINTS
    
    for d in days:
        for t in time_steps:
            
            # Photovoltaics
            model.addConstr(power["PV"][d][t] <= param["GHI"][d][t]/1e3 * devs["PV"]["eta"] * area["PV"])
            
            # Wind turbine
            model.addConstr(power["WT"][d][t] <= devs["WT"]["norm_power"][d][t] * cap["WT"])
            
            # Hydropower
            model.addConstr(power["WAT"][d][t] <= devs["WAT"]["potential"])
            
            # Solar thermal collector
            model.addConstr(heat["STC"][d][t] <= param["GHI"][d][t]/1e3 * devs["STC"]["eta"] * area["STC"])
        
            # Electric heat pump
            model.addConstr(heat["HP"][d][t] == power["HP"][d][t] * devs["HP"]["COP"][d][t])
            
            # Electric boiler
            model.addConstr(heat["EB"][d][t] == power["EB"][d][t] * devs["EB"]["eta_th"])
            
            # Compression chiller
            model.addConstr(cool["CC"][d][t] == power["CC"][d][t] * devs["CC"]["COP"])  
    
            # Absorption chiller
            model.addConstr(cool["AC"][d][t] == heat["AC"][d][t] * devs["AC"]["eta_th"])
            
            # Gas CHP
            model.addConstr(power["CHP"][d][t] == gas["CHP"][d][t] * devs["CHP"]["eta_el"])
            model.addConstr(heat["CHP"][d][t] == gas["CHP"][d][t] * devs["CHP"]["eta_th"])
            
            # Gas boiler
            model.addConstr(heat["BOI"][d][t] == gas["BOI"][d][t] * devs["BOI"]["eta_th"])
            
            # Gas heat pump
            model.addConstr(heat["GHP"][d][t] == gas["GHP"][d][t] * devs["GHP"]["COP"])
            
            # Biomass CHP
            model.addConstr(power["BCHP"][d][t] == biom["BCHP"][d][t] * devs["BCHP"]["eta_el"])
            model.addConstr(heat["BCHP"][d][t] == biom["BCHP"][d][t] * devs["BCHP"]["eta_th"])
            
            # Biomass boiler
            model.addConstr(heat["BBOI"][d][t] == biom["BBOI"][d][t] * devs["BBOI"]["eta_th"])
                        
            # Waste CHP
            model.addConstr(power["WCHP"][d][t] == waste["WCHP"][d][t] * devs["WCHP"]["eta_el"])
            model.addConstr(heat["WCHP"][d][t] == waste["WCHP"][d][t] * devs["WCHP"]["eta_th"])
            
            # Waste boiler
            model.addConstr(heat["WBOI"][d][t] == waste["WBOI"][d][t] * devs["WBOI"]["eta_th"])
            
            # Electrolyzer
            model.addConstr(hydrogen["ELYZ"][d][t] == power["ELYZ"][d][t] * devs["ELYZ"]["eta_el"])
            
            # Fuel cell  
            model.addConstr(power["FC"][d][t] == hydrogen["FC"][d][t] * devs["FC"]["eta_el"])
            if devs["FC"]["enable_heat_diss"]:   # Heat can also be dissipated
                model.addConstr(heat["FC"][d][t] <= hydrogen["FC"][d][t] * devs["FC"]["eta_th"])
            else:   # Heat must be used
                model.addConstr(heat["FC"][d][t] == hydrogen["FC"][d][t] * devs["FC"]["eta_th"])
            
            # Sabatier reactor
            model.addConstr(gas["SAB"][d][t] == hydrogen["SAB"][d][t] * devs["SAB"]["eta"])
            
    
    #%% GLOBAL ENERGY BALANCES
    
    for d in days:
        for t in time_steps:
            
            # Heating balance
            model.addConstr(heat["STC"][d][t] + heat["HP"][d][t] + heat["EB"][d][t] + heat["CHP"][d][t] + heat["BOI"][d][t] + heat["GHP"][d][t] + heat["BCHP"][d][t] + heat["BBOI"][d][t]+ heat["WCHP"][d][t] + heat["WBOI"][d][t] + heat["FC"][d][t] == dem["heat"][d][t] + heat["AC"][d][t] + ch["TES"][d][t])
    
            # Electricity balance
            model.addConstr(power["PV"][d][t] + power["WT"][d][t] + power["WAT"][d][t] + power["CHP"][d][t] + power["BCHP"][d][t] + power["WCHP"][d][t] + power["FC"][d][t] + power["from_grid"][d][t] == dem["power"][d][t] + power["HP"][d][t] + power["EB"][d][t] + power["CC"][d][t] + power["ELYZ"][d][t] + ch["BAT"][d][t] + power["to_grid"][d][t])
    
            # Cooling balance
            model.addConstr(cool["AC"][d][t] + cool["CC"][d][t] == dem["cool"][d][t] + ch["CTES"][d][t])  
            
            # Gas balance
            model.addConstr(gas["from_grid"][d][t] + gas["SAB"][d][t] == gas["CHP"][d][t] + gas["BOI"][d][t] + gas["GHP"][d][t] + ch["GS"][d][t] + gas["to_grid"][d][t])
            
            # Hydrogen balance
            model.addConstr(hydrogen["ELYZ"][d][t] + hydrogen["import"][d][t] == dem["hydrogen"][d][t] + hydrogen["FC"][d][t] + hydrogen["SAB"][d][t] + ch["H2S"][d][t])
            
            # Biomass balance
            model.addConstr(biom["import"][d][t] == biom["BCHP"][d][t] + biom["BBOI"][d][t])
            
            # Waste balance
            model.addConstr(waste["import"][d][t] == waste["WCHP"][d][t] + waste["WBOI"][d][t])

    #%% MEET PEAK DEMANDS OF UNCLUSTERED DEMANDS
        
    # Heating
    model.addConstr(cap["HP"] + cap["EB"]
                    + cap["CHP"] / devs["CHP"]["eta_el"] * devs["CHP"]["eta_th"] 
                    + cap["BOI"]
                    + cap["GHP"]
                    + cap["BCHP"] / devs["BCHP"]["eta_el"] * devs["BCHP"]["eta_th"]
                    + cap["BBOI"]
                    + cap["WCHP"] / devs["WCHP"]["eta_el"] * devs["WCHP"]["eta_th"]
                    + cap["WBOI"]
                    + cap["FC"] / devs["FC"]["eta_el"] * devs["FC"]["eta_th"]
                    >= param["peak_heat"])
                    
    # Cooling
    model.addConstr(cap["CC"] + cap["AC"] >= param["peak_cool"])
    
    # Power

    if param["peak_dem_met_conv"] == False:
        model.addConstr(cap["CHP"] + cap["BCHP"] + cap["WCHP"] + cap["FC"] + grid_limit_el >= param["peak_power"]) 
    else:
        model.addConstr(cap["PV"] + cap["WT"] + cap["WAT"] + cap["CHP"] + cap["BCHP"] + cap["WCHP"] + cap["FC"] + grid_limit_el >= param["peak_power"])
    
    # Hydrogen
    if (param["enable_supply_hydrogen"] == False) and devs["ELYZ"]["feasible"]:
        model.addConstr(cap["ELYZ"] >= param["peak_hydrogen"])



    #%% STORAGE DEVICES

    for device in ["TES", "CTES", "BAT", "H2S", "GS"]:
        for day in year:        
            for t in np.arange(1, len(time_steps)):

                # Energy balance: soc(t) = soc(t-1) + charge - discharge
                model.addConstr(soc[device][day][t] == soc[device][day][t-1] * (1-devs[device]["sto_loss"]) + ch[device][sigma[day]][t])

            # Transition between two consecutive days
            if day > 0:
                model.addConstr(soc[device][day][0] == soc[device][day-1][len(time_steps)-1] * (1-devs[device]["sto_loss"]) + ch[device][sigma[day]][0])

        # Cyclic year condition
        model.addConstr(soc[device][0][0] ==  soc[device][len(year)-1][len(time_steps)-1] * (1-devs[device]["sto_loss"]) + ch[device][sigma[0]][0])


    #%% SUM UP RESULTS

    ### Total energy import/feed-in ###
    # Total amount of gas taken from and to grid
    model.addConstr(from_gas_grid_total == sum(sum(gas["from_grid"][d][t] for t in time_steps) * param["day_weights"][d] for d in days))
    model.addConstr(to_gas_grid_total   == sum(sum(gas["to_grid"][d][t] for t in time_steps) * param["day_weights"][d] for d in days))

    # Total electric energy from and to grid
    model.addConstr(from_el_grid_total == sum(sum(power["from_grid"][d][t] for t in time_steps) * param["day_weights"][d] for d in days))
    model.addConstr(to_el_grid_total   == sum(sum(power["to_grid"][d][t] for t in time_steps) * param["day_weights"][d] for d in days))

    # Total amount of biomass imported
    model.addConstr(biom_import_total == sum(sum(biom["import"][d][t] for t in time_steps) * param["day_weights"][d] for d in days))

    # Total amount of waste imported
    model.addConstr(waste_import_total == sum(sum(waste["import"][d][t] for t in time_steps) * param["day_weights"][d] for d in days))

    # Total amount of hydrogen imported
    model.addConstr(hydrogen_import_total == sum(sum(hydrogen["import"][d][t] for t in time_steps) * param["day_weights"][d] for d in days))


    ### Costs ###
    # Costs/revenues for electricity
    model.addConstr(supply_costs_el  == from_el_grid_total  * param["price_supply_el"])
    model.addConstr(cap_costs_el     == grid_limit_el       * param["price_cap_el"])
    model.addConstr(rev_feed_in_el   == to_el_grid_total    * param["revenue_feed_in_el"])
    model.addConstr(rev_feed_in_el   <= param["revenue_feed_in_el"] * param["feed_in_el_limit"])

    # Costs/revenues for natural gas
    model.addConstr(supply_costs_gas == from_gas_grid_total * param["price_supply_gas"])
    model.addConstr(cap_costs_gas    == grid_limit_gas      * param["price_cap_gas"])
    model.addConstr(rev_feed_in_gas  == to_gas_grid_total   * param["revenue_feed_in_gas"])

    # Costs for biomass, waste and hydrogen
    model.addConstr(supply_costs_biom     == biom_import_total     * param["price_biomass"])
    model.addConstr(supply_costs_waste    == waste_import_total    * param["price_waste"])
    model.addConstr(supply_costs_hydrogen == hydrogen_import_total * param["price_hydrogen"])


    ### Supply limitations ###

    # Forbid/allow feed-in (user input)
    if param["enable_feed_in_el"] != True:
        model.addConstr(to_el_grid_total == 0)
        # Ensure alternative pathways for energy balance
        for d in days:
            for t in time_steps:
                model.addConstr(
                    power["PV"][d][t] + power["WT"][d][t] + power["WAT"][d][t] + power["CHP"][d][t] + 
                    power["BCHP"][d][t] + power["WCHP"][d][t] + power["FC"][d][t] == 
                    dem["power"][d][t] + power["HP"][d][t] + power["EB"][d][t] + 
                    power["CC"][d][t] + power["ELYZ"][d][t] + ch["BAT"][d][t]
                )
    if param["enable_feed_in_gas"] != True:
        model.addConstr(to_gas_grid_total == 0)
        # Ensure alternative pathways for gas balance
        for d in days:
            for t in time_steps:
                model.addConstr(
                    gas["from_grid"][d][t] + gas["SAB"][d][t] == gas["CHP"][d][t] + 
                    gas["BOI"][d][t] + gas["GHP"][d][t] + ch["GS"][d][t]
                )

    # Limitation of electricity supply (user input)
    if param["enable_supply_el"] == False:
        model.addConstr(from_el_grid_total == 0)
    if param["enable_cap_limit_el"] == True:
        model.addConstr(grid_limit_el <= param["cap_limit_el"])
    if param["enable_supply_limit_el"] == True:
        model.addConstr(from_el_grid_total <= param["supply_limit_el"])

    # Limitation of gas supply (user input)
    if param["enable_supply_gas"] != True:
        model.addConstr(from_gas_grid_total == 0)
    if param["enable_cap_limit_gas"] == True:
        model.addConstr(grid_limit_gas <= param["cap_limit_gas"])
    if param["enable_supply_limit_gas"] == True:
        model.addConstr(from_gas_grid_total <= param["supply_limit_gas"])

    # Limitation of biomass supply (user input)
    if param["enable_supply_biomass"] != True:
        model.addConstr(biom_import_total == 0)    
    if param["enable_supply_limit_biom"] == True:
        model.addConstr(biom_import_total <= param["supply_limit_biom"])

    # Limitation of waste supply (user input)
    if param["enable_supply_waste"] != True:
        model.addConstr(waste_import_total == 0)    
    if param["enable_supply_limit_waste"] == True:    
        model.addConstr(waste_import_total <= param["supply_limit_waste"])

    # Limitation of hydrogen supply (user input)
    if param["enable_supply_hydrogen"] != True:
        model.addConstr(hydrogen_import_total == 0)
    if param["enable_supply_limit_hydrogen"] == True:
        model.addConstr(hydrogen_import_total <= param["supply_limit_hydrogen"])


    #%% INVESTMENT COSTS

    

    new_method = True # The new method for calculating costs, as in Simulationsfahrplan.docx
    if new_method == True:
        t_clc = param["observation_time"]
        rate = param["interest_rate"]

        q = 1 + rate
        crf = (q ** t_clc * rate) / (q ** t_clc - 1)  # Capital recovery factor
        print(crf)

        b_years = [2024, 2025, 2030, 2035, 2040]
        gas_prices = [130, 106, 104, 103, 116]
        el_prices = [340, 349,	303, 302, 322]

        # Find the closest year to the observation time + 2024

        min_year = min(b_years, key=lambda x:abs(x-(t_clc + 2024)))

        id_min_year = b_years.index(min_year)

        prChange = {"el"   : 1 + (el_prices[id_min_year]/el_prices[0])**1/(min_year-2024),  # Price change factors per year for electricity
                    "gas"  : 1 + (gas_prices[id_min_year]/gas_prices[0])**1/(min_year-2024),  # Price change factors per year for natural gas
                    "infl" : 1.017}  # Price change factors per year for inflation

        b = {key: (1 - (prChange[key] / q) ** t_clc) / (q - prChange[key])
            for key in prChange.keys()}

        rval = {}
        for device in all_devs:
            
            life_time = devs[device]["life_time"]
            n = int(t_clc / life_time) # Number of replacements
            r = 0.1 

            if t_clc < 16:
                rval[device] = sum((rate/q)**(i * life_time) for i in range(0, n+1)) - ((r**(n * life_time) * ((n+1) * life_time - t_clc)) / (life_time * q**t_clc))
                print(rval[device])
            else:
                rval[device] = ((n+1) * life_time - t_clc) / life_time * (q ** (-t_clc))


            # rval[device] = ((n+1) * life_time - observation_time) / life_time * (q ** (-observation_time))

        # Total investment costs

        # !! În BuildingOT inv[device] e specific
            
        # Annual investment costs
        for device in all_devs:
            # INFO: BuildingOT - inv[device] e specific
            model.addConstr(c_inv[device] == crf * (1 - rval[device]) * cap[device] * devs[device]["inv_var"])
            
        # Operation and maintenance costs
        for device in all_devs:    
            # INFO: BuildingOT - f_serv = cost_om   
            model.addConstr(c_om[device] == crf * b["infl"] * devs[device]["cost_om"] * devs[device]["inv_var"])
            
        # Demand related costs

        for device in all_devs:

            gas_devices = {"CHP", "BOI", "GHP", "SAB"}
            el_devices = {"HP", "EB", "CC", "ELYZ", "FC"}

            gas_price = param["price_supply_gas"]
            el_price = param["price_supply_el"]

            dt = 1

            weight_days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

            if device in gas_devices:
                summation = 0
                for d in range(len(weight_days)):
                    for t in time_steps:
                        try:
                            summation += gas[device][d][t]
                        except:
                            pass

                model.addConstr(c_dem[device] == crf * b["gas"] * gas_price * dt * summation)
                
            if device in el_devices:

                summation = 0
                for d in range(len(weight_days)):
                    for t in time_steps:
                        try:
                            summation += power[device][d][t]
                        except:
                            pass
                
                model.addConstr(c_dem[device] == crf * b["el"] * el_price * dt * summation)

                model.addConstr(c_dem[device] == crf * b["el"] * el_price * dt * 
                                 sum(weight_days[d] * sum(power[device][d][t] for t in time_steps) for d in range(len(days))))
                

        # Total annual costs
        for device in all_devs:
            model.addConstr(c_total[device] == c_inv[device] + c_om[device] + c_dem[device])
    else:
        life_time = devs[device]["life_time"]
        observation_time = param["observation_time"]
        interest_rate = param["interest_rate"]
        q = 1 + param["interest_rate"]

        n = int(math.floor(observation_time / life_time))
        CRF = ((q**observation_time)*interest_rate)/((q**observation_time)-1)
        
        # Investment for replacements
        invest_replacements = sum((q ** (-i * life_time)) for i in range(1, n+1))

        # Residual value of final replacement
        res_value = ((n+1) * life_time - observation_time) / life_time * (q ** (-observation_time))

        if life_time > param["observation_time"]:
            ann_factor = (1 - res_value) * CRF 
        else:
            ann_factor = ( 1 + invest_replacements - res_value) * CRF 
        for device in all_devs:
            model.addConstr(inv[device] == devs[device]["inv_var"] * cap[device])  
            
        # Annual investment costs
        for device in all_devs:
            model.addConstr(c_inv[device] == inv[device] * ann_factor)
            
        # Operation and maintenance costs
        for device in all_devs:       
            model.addConstr(c_om[device] == devs[device]["cost_om"] * inv[device])
            
        # Total annual costs
        for device in all_devs:
            model.addConstr(c_total[device] == c_inv[device] + c_om[device])

    
    # CO2 feed_in constraint

    co2_feed_in_limit = param["co2_feed_in_limit"]  # Set your desired limit here, e.g., -100 kg CO2

    # Ensure the negative CO2 emissions from feed-in do not exceed the specified limit
    model.addConstr(
        (to_el_grid_total * param["co2_el_feed_in"] + to_gas_grid_total * param["co2_gas_feed_in"]) <= co2_feed_in_limit,
        "co2_feed_in_limit"
    )

    


    #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Set model parameters and execute calculation

    print("Precalculation and model set up done in %f seconds."  % (time.time() - start_time))

    # Set solver parameters
    model.Params.MIPGap   = 0.02  # ---,   gap for branch-and-bound algorithm
    # model.Params.method = 2     # ---,   -1: default, 0: primal simplex, 1: dual simplex, 2: barrier, etc.

    # Execute calculation
    start_time = time.time()
    model.setParam('OutputFlag', 0)
    model.optimize()
    print("Optimization done. (%f seconds.)" % (time.time() - start_time))


    #%% Check and save results

    # Check if optimal solution was found
    if model.Status in (3, 4) or model.SolCount == 0:  # "INFEASIBLE" or "INF_OR_UNBD"

        print("Optimization: No feasible solution found.")
        try:
            print("Try to calculate IIS.")
            model.computeIIS()
            model.write("model.ilp")
            print("IIS was calculated and saved as model.ilp")

        except:
            print("Could not calculate IIS.")
        return {}

    else:
        result_dir = "results"
        if not os.path.exists(result_dir):
            os.makedirs(result_dir)
            
        model.write(os.path.join(result_dir, "model.sol"))
        model.write(os.path.join(result_dir, "model.lp"))

        used_devices = [dev for dev in all_devs if cap[dev].X > 0.1]

        
        result_dict.update({
            "devices": {},
            "total_costs": {},
            "co2_emissions": {},
            "grid_flows": {}
        })


        for k in used_devices:
            
            result_dict["devices"][k] = {"cap": round(cap[k].X, 2)}


        # Total investment costs in EUR

        result_dict["total_costs"] = {
            "Description": "Total investment costs in EUR",

            "total_annualized_costs_objective": int(obj["tac"].X), #
            "total_annual_costs": int(sum(c_total[k].X for k in cap.keys())),
            "total_ann_inv_cost": int(sum(c_inv[k].X for k in cap.keys())),
            "total_om_cost": int(sum(c_om[k].X for k in cap.keys()))

        }
   
        co2_emissions = from_el_grid_total.X * param["co2_el_grid"] + from_gas_grid_total.X * param["co2_gas"] + biom_import_total.X * param["co2_biom"] + waste_import_total.X * param["co2_waste"] + hydrogen_import_total.X * param["co2_hydrogen"] - to_el_grid_total.X * param["co2_el_feed_in"] - to_gas_grid_total.X * param["co2_gas_feed_in"]
        # CO2 emissions
        result_dict["co2_emissions"] = {
        
            "Description": "Total CO2 emissions in kg/a",

            
            "total_co2_emissions": int(co2_emissions),
          
                

            "onsite": int((from_gas_grid_total.X * param["co2_gas"] + biom_import_total.X * param["co2_biom"] + waste_import_total.X * param["co2_waste"])),
            "credit_feedin": int((to_el_grid_total.X * param["co2_el_feed_in"] + to_gas_grid_total.X * param["co2_gas_feed_in"])),

            "generated due to electrity": int(from_el_grid_total.X * param["co2_el_grid"]),
            "won due to electricity feed in": int(to_el_grid_total.X * param["co2_el_feed_in"]),
            "generated due to gas": int(from_gas_grid_total.X * param["co2_gas"]),
            "won due to gas feed in": int(to_gas_grid_total.X * param["co2_gas_feed_in"]),
            "generated due to biom": int(biom_import_total.X * param["co2_biom"]),
            "generated due to waste": int(waste_import_total.X * param["co2_waste"]),
            "generated due to hydrogen": int(hydrogen_import_total.X * param["co2_hydrogen"])
        }

        result_dict["co2_emissions"]["tax_total"] = int(result_dict["co2_emissions"]["onsite"] * param["co2_tax"] * 1000)  # EUR

        # Grid flows (in and out) in MWh
        result_dict["grid_flows"] = {  

            "Description": "Total grid flows in kWh/a",

            "from_el_grid_total"  : int(from_el_grid_total.X)  ,  
            "to_el_grid_total"    : int(to_el_grid_total.X)  ,    
            "from_gas_grid_total" : int(from_gas_grid_total.X)  , 
            "to_gas_grid_total"   : int(to_gas_grid_total.X)  ,   
            "biom_import_total"   : int(biom_import_total.X)  ,   
            "waste_import_total"  : int(waste_import_total.X)  ,  
            "hydrogen_import_total": int(hydrogen_import_total.X) 
        }

        

        

        # Calculate maximum grid flows (electricity and gas)

        for k in ["from_grid", "to_grid"]:

            result_dict["grid_flows"]["max_el_" + k] = 0
            result_dict["grid_flows"]["max_gas_" + k] = 0

            for d in days:
                for t in time_steps:

                    if power[k][d][t].X > result_dict["grid_flows"]["max_el_" + k]:
                        result_dict["grid_flows"]["max_el_" + k] = power[k][d][t].X

                    if gas[k][d][t].X > result_dict["grid_flows"]["max_gas_" + k]:
                        result_dict["grid_flows"]["max_gas_" + k] = gas[k][d][t].X

            result_dict["grid_flows"]["max_el_" + k] = int(result_dict["grid_flows"]["max_el_" + k])
            result_dict["grid_flows"]["max_gas_" + k] = int(result_dict["grid_flows"]["max_gas_" + k])

        for k in ["from_grid", "to_grid"]:
            result_dict["grid_flows"]["max_gas_" + k] = 0
            for d in days:
                for t in time_steps:
                    if gas[k][d][t].X > result_dict["grid_flows"]["max_gas_" + k]:
                        result_dict["grid_flows"]["max_gas_" + k] = gas[k][d][t].X
            result_dict["grid_flows"]["max_gas_" + k] = int(result_dict["grid_flows"]["max_gas_" + k])

        result_dict["grid_flows"]["max_biom"] = 0
        result_dict["grid_flows"]["max_waste"] = 0
        result_dict["grid_flows"]["max_hydrogen"] = 0
        
        for d in days:
            for t in time_steps:
                if biom["import"][d][t].X > result_dict["grid_flows"]["max_biom"]:
                    result_dict["grid_flows"]["max_biom"] = biom["import"][d][t].X

                if waste["import"][d][t].X > result_dict["grid_flows"]["max_waste"]:\
                    result_dict["grid_flows"]["max_waste"] = waste["import"][d][t].X  

                if hydrogen["import"][d][t].X > result_dict["grid_flows"]["max_hydrogen"]:
                    result_dict["grid_flows"]["max_hydrogen"] = hydrogen["import"][d][t].X        
            
        result_dict["grid_flows"]["max_biom"] = int(result_dict["grid_flows"]["max_biom"])
        result_dict["grid_flows"]["max_waste"] = int(result_dict["grid_flows"]["max_waste"])
        result_dict["grid_flows"]["max_hydrogen"] = int(result_dict["grid_flows"]["max_hydrogen"])


        result_dict["supply_costs"] = {
            "Description": "Total supply costs in EUR",

            "supply_costs_el"    : int(supply_costs_el.X),
            "cap_costs_el"       : int(cap_costs_el.X),
            "total_el_costs"     : int(supply_costs_el.X + cap_costs_el.X),
            "rev_feed_in_el"     : int(rev_feed_in_el.X),

            "supply_costs_gas"   : int(supply_costs_gas.X),
            "cap_costs_gas"      : int(cap_costs_gas.X),
            "total_gas_costs"    : int(supply_costs_gas.X + cap_costs_gas.X),
            "rev_feed_in_gas"    : int(rev_feed_in_gas.X),

            "supply_costs_biom"  : int(supply_costs_biom.X),
            "supply_costs_waste" : int(supply_costs_waste.X),
            "supply_costs_hydrogen" : int(supply_costs_hydrogen.X)
        }


        # Prepare time series of renewable curtailment
        power["PV_curtail"] = {}
        power["WT_curtail"] = {}
        power["WAT_curtail"] = {}
        heat["STC_curtail"] = {}
        for d in days:
            power["PV_curtail"][d] = {}
            power["WT_curtail"][d] = {}
            power["WAT_curtail"][d] = {}
            heat["STC_curtail"][d] = {}
            for t in time_steps:
                power["PV_curtail"][d][t] = devs["PV"]["norm_power"][d][t] * devs["PV"]["G_stc"] * devs["PV"]["eta"] * area["PV"].X - power["PV"][d][t].X
                power["WT_curtail"][d][t] = devs["WT"]["norm_power"][d][t] * cap["WT"].X - power["WT"][d][t].X
                power["WAT_curtail"][d][t] = np.min([cap["WAT"].X, devs["WAT"]["potential"]]) - power["WAT"][d][t].X
                heat["STC_curtail"][d][t] = devs["STC"]["specific_heat"][d][t] * area["STC"].X - heat["STC"][d][t].X


        if "PV" in used_devices:
            result_dict["devices"]["PV"]["curtailed"] = int((sum(sum(power["PV_curtail"][d][t] for t in time_steps) * param["day_weights"][d] for d in days))/1000)
        if "WT" in used_devices:
            result_dict["devices"]["WT"]["curtailed"] = int((sum(sum(power["WT_curtail"][d][t] for t in time_steps) * param["day_weights"][d] for d in days))/1000)
        if "WAT" in used_devices:
            result_dict["devices"]["WAT"]["curtailed"] = int((sum(sum(power["WAT_curtail"][d][t] for t in time_steps) * param["day_weights"][d] for d in days))/1000)
        if "STC" in used_devices:
            result_dict["devices"]["STC"]["curtailed"] = int((sum(sum(heat["STC_curtail"][d][t] for t in time_steps) * param["day_weights"][d] for d in days))/1000)


        # Calculate generation in kWh
        eps = 0.01
        for k in used_devices:
            # Initialize the 'generated' key for the current device
            result_dict["devices"][k]["generated"] = 0

            if k in ["STC", "HP", "EB", "BOI", "GHP", "BBOI", "WBOI"]:
                result_dict["devices"][k]["generated"] = int(sum(sum(heat[k][d][t].X for t in time_steps) * param["day_weights"][d] for d in days))
            elif k in ["CC", "AC"]:
                result_dict["devices"][k]["generated"] = int(sum(sum(cool[k][d][t].X for t in time_steps) * param["day_weights"][d] for d in days))
            elif k in ["PV", "WT", "WAT", "CHP", "BCHP", "WCHP", "ELYZ", "FC"]:
                result_dict["devices"][k]["generated"] = int(sum(sum(power[k][d][t].X for t in time_steps) * param["day_weights"][d] for d in days))
                if k in ["CHP", "BCHP", "WCHP"]:
                  generated = {
                        "power": int(sum(sum(power[k][d][t].X for t in time_steps) * param["day_weights"][d] for d in days)),
                        "heat": int(sum(sum(heat[k][d][t].X for t in time_steps) * param["day_weights"][d] for d in days))
                  }
                  result_dict["devices"][k]["generated"] = generated
            
            # Calculate full load hours
            if cap[k].X > eps:

                if k in ["CHP", "BCHP", "WCHP"]:
                    total_generated = result_dict["devices"][k]["generated"]["power"] + result_dict["devices"][k]["generated"]["heat"]
                    result_dict["devices"][k]["full_load_hours"] = int(total_generated / cap[k].X)
                else:
                    result_dict["devices"][k]["full_load_hours"] = int(result_dict["devices"][k]["generated"] / cap[k].X)
            else:
                result_dict["devices"][k]["full_load_hours"] = 0

        # result_dict["ELYZ"]["generated"] = int(sum(sum(power["ELYZ"][d][t].X * devs["ELYZ"]["eta_el"]for t in time_steps) * param["day_weights"][d] for d in days)) 

        # result_dict["SAB"]["generated"] = sum(sum(gas[k][d][t].X for t in time_steps) * param["day_weights"][d] for d in days)  

        # Area of PV and STC
        
        if "PV" in used_devices:
            result_dict["devices"]["PV"]["area"] = int(area["PV"].X)
        if "STC" in used_devices:
            result_dict["devices"]["STC"]["area"] = int(area["STC"].X)
        

        # Calculate charge cycles of storages
        for k in used_devices:
            if k in ["TES", "CTES", "BAT", "H2S", "GS"]:
                if cap[k].X > eps:
                    result_dict["devices"][k]["charge_cycles"] = int(sum(sum(abs(ch[k][d][t].X)/2 for t in time_steps) * param["day_weights"][d] for d in days) / cap[k].X)
                else:
                    result_dict["devices"][k]["charge_cycles"] = 0

            # Calculate volume of thermal storages
            if k in ["TES", "CTES"]:
                result_dict["devices"][k]["volume"] = round(cap[k].X / (param["c_w"] * param["rho_w"] * devs[k]["delta_T"]) * 3600, 1)
        

        # Print cost of all devices

        for k in used_devices:
            result_dict["devices"][k]["cost"] = int(c_total[k].X)

        # Calculate share of renewables

        shared_renew = 0

        for k in ["PV", "WT", "WAT", "STC"]:
            if k in used_devices:
                shared_renew += result_dict["devices"][k]["generated"]

        shared_renew = shared_renew/(shared_renew + from_el_grid_total.X + from_gas_grid_total.X + biom_import_total.X + waste_import_total.X + hydrogen_import_total.X) * 100



        result_dict["percent_of_renewable_sources"] = round(shared_renew, 1)
        

        ### REWRITE DESIGN DAYS IN FULL YEAR ###

        tech_list = ["power_PV", "power_PV_curtail",
                        "power_WT", "power_WT_curtail",
                        "power_WAT", "power_WAT_curtail",
                        "heat_STC", "heat_STC_curtail",

                        "heat_HP", "power_HP",
                        "heat_EB", "power_EB",
                        "cool_CC", "power_CC",
                        "cool_AC", "heat_AC",

                        "power_CHP", "heat_CHP", "gas_CHP",
                        "heat_BOI", "gas_BOI",
                        "heat_GHP", "gas_GHP",

                        "power_BCHP", "heat_BCHP", "biom_BCHP",
                        "heat_BBOI", "biom_BBOI",
                        "power_WCHP", "heat_WCHP", "waste_WCHP",
                        "heat_WBOI", "waste_WBOI",

                        "power_ELYZ", "hydrogen_ELYZ",
                        "power_FC", "heat_FC", "hydrogen_FC",
                        "hydrogen_SAB", "gas_SAB",

                        "ch_TES", "ch_CTES", "ch_BAT", "ch_GS", "ch_H2S",

                        "dem_heat", "dem_cool", "dem_power", "dem_hydrogen",

                        "biom_import", "waste_import", "hydrogen_import", "power_to_grid", "power_from_grid", "gas_from_grid", "gas_to_grid",
                        ]

        soc_list = ["soc_TES", "soc_CTES", "soc_BAT", "soc_GS", "soc_H2S"]

        # Arrange full time series with 8760 steps
        full = {}
        for item in tech_list:
            full[item] = np.zeros(8760)
        # Get list of days used as type days
        z = param["day_matrix"]
        typedays = []
        for d in range(365):
            if any(z[d]):
                typedays.append(d)
        # Arrange time series
        for d in range(365):
            match = np.where(z[:,d] == 1)[0][0]
            typeday = np.where(typedays == match)[0][0]
            for item in tech_list:
                m, tech = item.split("_", 1)
                if not m == "soc":
                    if m == "power":
                        m_arr = power
                    elif m == "heat":
                        m_arr = heat
                    elif m == "cool":
                        m_arr = cool
                    elif m == "hydrogen":
                        m_arr = hydrogen
                    elif m == "gas":
                        m_arr = gas
                    elif m == "biom":
                        m_arr = biom
                    elif m == "waste":
                        m_arr = waste
                    elif m == "ch":
                        m_arr = ch
                    elif m == "dem":
                        m_arr = dem
                    for t in range(24):
                        if m == "dem" or tech == "PV_curtail" or tech == "STC_curtail" or tech == "WT_curtail" or tech == "WAT_curtail":
                            full[item][24*d+t] = m_arr[tech][typeday][t]
                        else:
                            full[item][24*d+t] = m_arr[tech][typeday][t].X
                        # print("full["+item+"][" + str(24*d+t) + "] = m_arr["+tech+"]["+str(typeday)+"]["+str(t)+"].X)")

        for item in soc_list:
            m, tech = item.split("_", 1)
            if m == "soc":
                full[item] = np.zeros(8760)
                for d in range(365):
                    for t in range(24):
                        full[item][24*d+t] = soc[tech][d][t].X

        ### CALC MONTHLY VALS ###
        month_tuple = ("Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec")
        days_sum = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334, 365]

        # Calc ambient heat and mean COP

        if "HP" in used_devices:
            full["amb_heat_HP"] = full["heat_HP"] - full["power_HP"]

            total_heat_HP = np.sum(full["heat_HP"])
            total_power_HP = np.sum(full["power_HP"])

            if total_power_HP == 0:
                # Handle the case where total_power_HP is zero to avoid division by zero
                result_dict["devices"]["HP"]["mean_COP"] = np.nan  # or use a default value, e.g., 0 or float('inf')
            else:
                result_dict["devices"]["HP"]["mean_COP"] = round(total_heat_HP / total_power_HP, 2)


        # Remove all devices with generated = 0

        to_remove = []
        for k in used_devices:
            if k not in ["BAT", "GS", "H2S", "TES", "CTES"]:
                if k in ["CHP", "BCHP", "WCHP"]:
                    if result_dict["devices"][k]["generated"]["power"] == 0 and result_dict["devices"][k]["generated"]["heat"] == 0:
                        to_remove.append(k)
                else:
                    if result_dict["devices"][k]["generated"] == 0:
                        to_remove.append(k)
        
        for k in to_remove:
            used_devices.remove(k)
            result_dict["devices"].pop(k, None)
                

        # Calculate the size of every device

        # Size is the peak generation in kW, not in kWh

        for k in used_devices:

            if k in ["CHP", "BCHP", "WCHP"]:
                size = max(heat[k][d][t].X + power[k][d][t].X for d in days for t in time_steps)
                result_dict["devices"][k]["peak_generation"] = round(size, 2)
            if "generated" in result_dict["devices"][k]:
                try:
                    if k in ["HP", "EB", "CC", "ELYZ", "FC", "STC", "AC", "CC"]:
                        size = max(heat[k][d][t].X for d in days for t in time_steps)
                        result_dict["devices"][k]["peak_generation"] = round(size, 2)
                    else:
                        size = max(power[k][d][t].X for d in days for t in time_steps)
                        result_dict["devices"][k]["peak_generation"] = round(size, 2)
                except KeyError:
                    result_dict["devices"][k]["peak_generation"] = 0

        

        """ 
        monthly_val = {}
        year_peak = {}
        year_sum = {}
        for m in ["power_PV", "power_WT", "power_WAT", "heat_STC", "heat_HP", "amb_heat_HP"]:
            monthly_val[m] = {}
            year_peak[m] = int(np.max(full[m]))
            year_sum[m] = int(np.sum(full[m]))
            for month in range(12):
                monthly_val[m][month_tuple[month]] = sum(full[m][t] for t in range(days_sum[month]*24, days_sum[month+1]*24))

        result_dict["monthly_val"] = monthly_val
        result_dict["year_peak"].update(year_peak)
        result_dict["year_sum"].update(year_sum)
        """

         #  create_excel_file.create_excel_file(full, dem, devs, "45484", time_steps, days)

        # Remove all keys that have "cap" = 0
        #for k in all_devs:
        #    if cap[k].X < eps:
        #        result_dict.pop(k, None)


        return result_dict

# %%
