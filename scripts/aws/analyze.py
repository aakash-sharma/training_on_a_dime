from datetime import datetime
import json
import matplotlib.pyplot as plt

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


    for instance in all_y_axis:
        y_axis = all_y_axis[instance]
        for i in range(len(y_axis)):
            y_axis[i] = max(0, y_axis[i])
    
    print(all_y_axis)

def avg_lifespan(logs):

    for instance in instance_types:
        lifespan_buckets[instance] = []

    end_time = datetime.strptime(TL[-1], '%Y-%m-%dT%H:%M:%S.000Z')
    print(end_time)

    for instance_id in logs:
        instance = (logs[instance_id][0][0], logs[instance_id][0][1])
        st_time = datetime.strptime(logs[instance_id][1], '%Y-%m-%dT%H:%M:%S.000Z')

        lifespan = 0

        if logs[instance_id][2] != -1:
            lifespan = datetime.strptime(logs[instance_id][2], '%Y-%m-%dT%H:%M:%S.000Z') - st_time
        else:
            lifespan = end_time - st_time

        if lifespan.total_seconds() < 0:
            print(logs[instance_id])


        lifespan_buckets[instance].append(lifespan.total_seconds())
       
    print(lifespan_buckets) 
    
def plot():

    #fig1, axs1 = plt.plot()    
    instance = ("k80", 1)
    y_axis = all_y_axis[instance]
    plt.plot([i for i in range(len(TL))], y_axis)
    plt.title("Spot instance (p2.xlarge) availability")
    plt.xlabel('Normalized time interval')
    plt.ylabel('Availability')

    plt.show()

    y_axis = lifespan_buckets[instance]
    y_axis = [lifespan for lifespan in y_axis if lifespan > 0]
    x_axis = [i for i in range(len(y_axis))]
    plt.plot(x_axis, y_axis)
    plt.title("Instance lifespan")
    plt.ylabel('Seconds')
    plt.xlabel('Normalized instance Id')
    plt.show()


    

def main():
    with open('dict_snapshot', 'r') as dict_snapshot:
        logs = json.load(dict_snapshot)
    with open('dict_snapshot2', 'r') as dict_snapshot2:
        logs2 = json.load(dict_snapshot2)


    get_timeline(logs2)
    instances_over_time(logs, logs2)
    avg_lifespan(logs)

    plot()


if __name__ == '__main__':
    main()

