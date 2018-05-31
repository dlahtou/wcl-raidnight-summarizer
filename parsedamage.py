## this file takes a folder full of damage log files and prints the top 10

import json
from os import listdir
import os.path

damage_list = []

for filename in listdir('First-fights'):
    with open(os.path.join('First-fights',filename),'r') as open_file:
        damage_data = json.load(open_file)
    total_time = damage_data['totalTime']
    for entry in damage_data['entries']:
        damage_list.append((entry['name'],entry['total']/total_time,filename.split('.')[0]))

damage_list = sorted(damage_list,key=lambda x: x[1],reverse=True)

print("Top dps:")
for name,dps,boss in damage_list[:10]:
    print(name + ": %dk dps on %s" % (dps,boss))