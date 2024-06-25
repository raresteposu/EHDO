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


devices_to_use = ["HP","BOI", "CHP","BCHP","AC", "PV", "STC", "EB", "BBOI", "BAT"] # Feasible devices

param, devs, dem, result_dict = load_params.load_params(building, size, year, devices_to_use)

param["observation_time"] = 10
devs ["PV"]["life_time"] = 5
param["enable_feed_in_el"] = True
param["revenue_feed_in_el"] = 0.01


result_dict = optim_model.run_optim(devs, param, dem, result_dict)

result_dict_name = "results/" + building +".json"

with open(result_dict_name, 'w') as json_file:
    json.dump(result_dict, json_file, indent=4)


'''

✅   obs_time = 10 | PV life_time = 20 | enable_feed_in_el = True | revenue_feed_in_el = 0.01
--------------------------------------------
❌   obs_time = 10 | PV life_time = 5  | enable_feed_in_el = True | revenue_feed_in_el = 0.01
        - Infeasible #TODO: Asta trebe rezolvat
--------------------------------------------
❌   obs_time = 20 | PV life_time = 20 | enable_feed_in_el = True | revenue_feed_in_el = 0.01
     - cap = max și cost sunt foarte mici
     - ❗ Cu metoda veche de calculat merge
--------------------------------------------
❌   obs_time = 20 | PV life_time = 20 | enable_feed_in_el = False | revenue_feed_in_el = 0.01 
     - Infeasible
❌   obs_time = 20 | PV life_time = 20 | enable_feed_in_el = True | revenue_feed_in_el = 0.00 
     - cap = max și cost sunt foarte mici
-------------------------------------------


'''

#TODO: Wenn enable_feed_in_el = False, dann ist manchmal infeasible, weil die ganze Strom kann nicht weggeworfen werden. Die model funktioniert aber wenn revenue_feed_in_el = 0.00 ist (also preismaßig egal).

# --------------------------------------

"""

Sorry, dass ich nicht früher geschrieben habe, aber ich habe viel länger gebraucht, als ich dachte. 

Ich habe vielleicht das Aufgabe missverstanden und mehrere Kombinationen von obs_time und objectives ausprobiert (z.B. für obs_time < 16, um das Objective zu haben, die Kosten zu minimieren und gleichzeitig die Emissionen niedrig, aber negativ zu halten, und für obs_time > 16, um die Emissionen null zu machen. Vieles hat nicht funktioniert, entweder wegen die neue Kostenformula oder weil die parameters irgenwie nicht mit einander kompatibel waren.

Na ja, wenn ich nur für obs_time = 10 gearbeitet hätte, wäre ich in 2 Studenten statt in 15 fertig gewesen.

Ich habe aber noch ein paar Fragen, obwohl ich denke ich kann die selbstantworten, da jetz funktionert alles mit obs_time = 10.

---

1) Ich verstehe nicht wirklich, warum die obs_time 10 Jahre betragen sollte, wenn das Ziel Null-Emissionen bis 2040 ist (also obs_time = 16). 

2) Woher stammt die rval-Formel? Ich möchte mehr ein bisschen in sie schauen, weil ich nicht viel Sinn für mich machen. Zum Beispiel ist der rval eines Geräts mit life_time = 5 größer als für das gleiche Gerät mit life_time = 8. Die c_inv wird als crf * (1-rval) * cap berechnet, so dass die Kosten niedriger sind (obwohl sie wegen der Replacements höher sein sollten) Warum multiplizieren wir nicht einfach den c_inv mit der Anzahl der Replacements (also int(t_clc/life_time)?

3) Warum verwenden wir nicht auch Wärmepumpen zur Kühlung? Das wäre im Code leicht zu implementieren.

---

Willst du die aktuelle ergebnisse sehen per email, oder sollen wir bis Donnerstag warten?

Rareș

"""

# --------------------------------------


#TODO: Should we also use heatpumps for cooling?





















# Run post-processing
#post_processing.run(dir_results)
#post_processing.run(os.path.join(os.path.abspath(os.getcwd()), "Results", "test"))

    