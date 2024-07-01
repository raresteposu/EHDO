import json
import matplotlib.pyplot as plt
import numpy as np

def plot_demands_device(json_data):
    """
    Plots 3 bar charts, one for each demand type (heat, cool, power) showing the total demand and the generation of each device.
    """
    # Extract data
    demands = json_data['demands']["sum"]
    devices = json_data['devices']
    
    demand_types = ['heat', 'cool', 'power']
    
    device_values = {}
    for d in devices:
        if 'generated' in devices[d]:
            if isinstance(devices[d]['generated'], dict):
                for t in demand_types:
                    if t in devices[d]['generated']:
                        if d not in device_values:
                            device_values[d] = {t: devices[d]['generated'][t]}
                        else:
                            device_values[d][t] = devices[d]['generated'][t]
            else:  # Single number
                if d in ["PV"]:
                    device_values[d] = {"power": devices[d]['generated']}
                elif d in ["STC", "BOI", "EB", "BBOI", "WBOI"]:
                    device_values[d] = {"heat": devices[d]['generated']}
                elif d in ["AC", "CC"]:
                    device_values[d] = {"cool": devices[d]['generated']}
    
    # Grid 

    # Plot
    fig, axs = plt.subplots(1, 3, figsize=(18, 6), sharey=True)
    
    for i, t in enumerate(demand_types):
        total_demand = demands[t]
        axs[i].bar(['Total'], total_demand, label=f'Total {t.capitalize()} Demand')
        
        for device in device_values:
            if t in device_values[device]:
                axs[i].bar([device], device_values[device][t], label=device)
        
        axs[i].set_title(f'{t.capitalize()} Demand')
        axs[i].set_ylabel('Energy (kWh)')
        axs[i].legend()
    
    plt.tight_layout()
    plt.show()



file_name = "ac_istzustand"
json_path = "./results/"+file_name+".json"
with open(json_path) as f:
    data = json.load(f)
plot_demands_device(data)
