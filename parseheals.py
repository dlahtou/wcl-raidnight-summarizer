## this file takes a heal log and returns the top healer

import json

with open('first_heal_log.json','r') as open_file:
    heal_data = json.load(open_file)

total_time = heal_data['totalTime']

top_healer = "None"
total_healing = 0

for entry in heal_data['entries']:
    if entry['total'] > total_healing:
        total_healing = entry['total']
        top_healer = entry['name']

hps = int(round(total_healing/total_time))

print("Top Healer: %s with %s healing!" % (top_healer,total_healing))
print("HPS: " + str(hps) + "k")