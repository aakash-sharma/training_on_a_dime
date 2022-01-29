
from datetime import datetime
'''
sample_dict = {"i-03e566005ce6096f7": [["k80", 1], "2022-01-22T17:01:29.000Z", "2022-01-22T17:50:58.000Z"], "i-03dfabd6ab2fe1211": [["k80", 1], "2022-01-22T17:07:56.000Z", "2022-01-22T18:41:38.000Z"], "i-0a38568da603a6b15": [["k80", 1], "2022-01-22T17:19:36.000Z", "2022-01-22T17:56:35.000Z"], "i-03ce24b9c085ec5cf": [["k80", 1], "2022-01-22T17:26:03.000Z", -1]}
'''

import ast
from collections import OrderedDict

with open('dict_snapshot') as f:
    dict_data=f.read()

#sample_dict=json.loads(dict_data)
sample_dict = ast.literal_eval(dict_data)


def convert_to_seconds(timestamp):
    t = timestamp.split(':')
    hours=int(t[0])
    minutes=int(t[1])
    seconds=int(t[2])
    total_seconds = hours*3600+minutes*60+seconds
    return total_seconds


def convert_to_datetime(d):
    ymdhms=datetime.strptime(d, '%Y-%m-%dT%H:%M:%S.000Z')
    return ymdhms



def avg_lifespan(sample_dict):
    lifespan_list=[]
    for i in sample_dict:
        if sample_dict[i][2]!=-1:
            lifespan_list.append(convert_to_datetime(sample_dict[i][2]) - convert_to_datetime(sample_dict[i][1]))
    return lifespan_list

#Excel could've made this, didn't need it
def histogram_maker(sorted_final_avg_list, bin_size=10):
    hist_dict=OrderedDict()
    max_val_r=round(sorted_final_avg_list[-1],-1) #round up max value in list to nearest 10
    start=1

    while start<=max_val_r:
        if (start,start+9) not in hist_dict:
            hist_dict[(start,start+9)]=0
        start=start+10

    for i in sorted_final_avg_list:
        for j in hist_dict:
            if j[0]<=i and i<=j[1]:
                hist_dict[j]+=1

    for i in hist_dict:
        print(i,hist_dict[i])

    



avg_list = avg_lifespan(sample_dict)
final_avg_list=[]
print('avg_list')
for i in avg_list:
    final_avg_list.append(float(convert_to_seconds(str(i))/60))
final_avg_list.sort()
#print(final_avg_list)

for i in final_avg_list:
    print(i)

N=len(final_avg_list)

low=final_avg_list[0]
median=final_avg_list[N//2]
high=final_avg_list[N-1]


print('low',low,'median',median,'high',high)
#histogram_maker(final_avg_list)




a=convert_to_datetime("2022-01-22T17:01:29.000Z")-convert_to_datetime("2022-01-22T17:01:29.000Z")
n=0

for i in avg_list:
    a+=i
    n+=1

a=a/n
print('Average lifespan:')
print(a)

