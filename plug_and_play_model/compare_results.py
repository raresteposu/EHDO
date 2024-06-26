import json

def load_json(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def compare_demands(demands1, demands2):
    demand_diff = {}
    for key in demands1['sum']:
        demand_diff[key] = demands2['sum'].get(key, 0) - demands1['sum'].get(key, 0)
    return demand_diff

def compare_costs(costs1, costs2):
    cost_diff = {}
    for key in costs1:
        if key != "Description":
            cost_diff[key] = costs2.get(key, 0) - costs1.get(key, 0)
    return cost_diff

def compare_devices(devices1, devices2):
    device_diff = {}
    all_devices = set(devices1.keys()).union(set(devices2.keys()))
    for device in all_devices:
        device_diff[device] = {}
        if device in devices1 and device in devices2:
            for key in devices1[device]:
                if key in ["cap", 'cost']:
                    device_diff[device][key] = devices2[device].get(key, 0) - devices1[device].get(key, 0)
        elif device in devices1:
            device_diff[device] = {"removed": devices1[device]}
        else:
            device_diff[device] = {"added": devices2[device]}
    return device_diff

def generate_report(demand_diff, cost_diff, device_diff, output_path):
    with open(output_path, 'w') as file:
        file.write("Comparison\n")
        file.write("=================\n\n")
        
        file.write("Demand Differences:\n")
        for key, value in demand_diff.items():
            if value > 0:
                file.write(f"  The '{key}' demand in Sanierungszustand is with {round(value,2)} bigger then in the Istzustand\n")
            elif value < 0:
                file.write(f"  The '{key}' demand in Sanierungszustand is with {abs(round(value,2))} smaller then in the Istzustand\n")
            else:
                file.write(f"  The '{key}' demand is the same in both Zustands\n")
        file.write("\n")
        
        file.write("Cost Differences:\n")
        for key, value in cost_diff.items():
            if key == "total_annual_costs":
                if value > 0:
                    file.write(f"  Total annual costs are with {round(value,2)} bigger in Sanierungzustand\n")
                elif value < 0:
                    file.write(f"  Total annual costs are with {abs(round(value,2))} smaller in Sanierungzustand\n")
                else:
                    file.write("  Total annual costs are the same in both Zustands\n")

        file.write("\n")
        
        file.write("Device Differences:\n")
        for device, diffs in device_diff.items():
            file.write(f"  {device}:\n")
            for key, value in diffs.items():
                if key == "removed":
                    file.write(f"    - Removed: {value}\n")
                elif key == "added":
                    file.write(f"    - Added: {value}\n")
                else:
                    if key in ["cap", 'cost']:
                        if value > 0:
                            file.write(f"   The {key} is with {round(value,2)} bigger in Sanierungzustand\n")
                        elif value < 0:
                            file.write(f"   The {key} is with {abs(round(value,2))} smaller in Sanierungzustand\n")
                        else:
                            file.write(f"   The {key} is the same in both Zustands\n")
            file.write("\n")

if __name__ == "__main__":
    file1_path = "./results/ac_istzustand.json"
    file2_path = "./results/ac_sanierterzustand.json"
    output_path = "./results/ac_comparison.txt"
    
    json1 = load_json(file1_path)
    json2 = load_json(file2_path)
    
    demand_diff = compare_demands(json1["demands"], json2["demands"])
    cost_diff = compare_costs(json1["total_costs"], json2["total_costs"])
    device_diff = compare_devices(json1["devices"], json2["devices"])
    
    generate_report(demand_diff, cost_diff, device_diff, output_path)
    
    print(f"Comparison report generated: {output_path}")
