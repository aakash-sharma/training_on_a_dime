from datetime import datetime
import json
from availability import instance_types

TL = []
all_y_axis = {}
lifespan_buckets = {}

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

def avg_lifespan(logs):

    for instance in instance_types:
        lifespan_buckets[instance] = []

    end_time = datetime.strptime(TL[-1], '%Y-%m-%dT%H:%M:%S.000Z')

    for instance_id in logs:
        instance = (logs[instance_id][0][0], logs[instance_id][0][1])
        st_time = datetime.strptime(logs[instance_id][1], '%Y-%m-%dT%H:%M:%S.000Z')

        lifespan = 0

        if logs[instance_id][2] != -1:
            lifespan = datetime.strptime(logs[instance_id][2], '%Y-%m-%dT%H:%M:%S.000Z') - st_time
        else:
            lifespan = end_time - st_time


        lifespan_buckets[instance].append(lifespan.total_seconds())
       
    print(lifespan_buckets) 
    

        

def main():
    with open('dict_snapshot.bak', 'r') as dict_snapshot:
        logs = json.load(dict_snapshot)
    with open('dict_snapshot2.bak', 'r') as dict_snapshot2:
        logs2 = json.load(dict_snapshot2)


    get_timeline(logs2)
    instances_over_time(logs, logs2)
    avg_lifespan(logs)

    




if __name__ == '__main__':
    main()

