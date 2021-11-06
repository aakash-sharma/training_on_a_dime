from datetime import datetime
import json
from availability import instance_types

TL = []
all_y_axis = {}

def get_timeline(logs2):

    for ts in sorted(logs2.keys()):
        TL.append(ts)

def instances_over_time(logs, logs2):

    for instance in instance_types:
        all_y_axis[instance] = [0] * len(TL) 

    i = 1
            
    for ts in sorted(logs2.keys()):
        instance_id = logs2[ts][0]
        if instance_id == None:
            continue

        curr_instance = (logs[instance_id][0][0], logs[instance_id][0][1])
        
        for instance in all_y_axis:
            y_axis = all_y_axis[instance]
            if instance == curr_instance:
                y_axis[i] = y_axis[i-1] + logs2[ts][1]
            else:
                y_axis[i] = y_axis[i-1]

        i += 1

    
    print(all_y_axis)

        

def main():
    with open('dict_snapshot.bak', 'r') as dict_snapshot:
        logs = json.load(dict_snapshot)
    with open('dict_snapshot2.bak', 'r') as dict_snapshot2:
        logs2 = json.load(dict_snapshot2)


    get_timeline(logs2)
    instances_over_time(logs, logs2)

    




if __name__ == '__main__':
    main()

