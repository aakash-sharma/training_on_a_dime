import argparse
from datetime import datetime
import signal
import json
import subprocess
import sys
import time
import os
from shutil import copy


MAX_INSTANCES = 2
instances = {}
instance_types = {
    ("v100", 1): "p3.2xlarge",
    ("v100", 4): "p3.8xlarge",
    ("v100", 8): "p3.16xlarge",
    ("k80", 1): "p2.xlarge",
    ("k80", 8): "p2.8xlarge",
    ("k80", 16): "p2.16xlarge",
}

logs = {}
logs2 = {}

def persist_dict():
    with open('dict_snapshot', 'w') as dict_snapshot:
        dict_snapshot.write(json.dumps(logs))
    with open('dict_snapshot2', 'w') as dict_snapshot2:
        dict_snapshot2.write(json.dumps(logs2))

def signal_handler(sig, frame):
    global instances
    # Clean up all instances when program is interrupted.
    for (zone, gpu_type, num_gpus) in instances:
        for instance in instances[(zone, gpu_type, num_gpus)]:
            sir_id = instance[0]
            instance_id = instance[1]
            if sir_id is not None:
                delete_spot_instance(zone, sir_id, instance_id)

    logs2[datetime.now().strftime('%Y-%m-%dT%H:%M:%S.000Z')] = [None, 0]
    persist_dict()
    sys.exit(0)

def signal_handler2(sig, frame):
    global instances
    # Clean up all instances when program is interrupted.
    for (zone, gpu_type, num_gpus) in instances:
        for instance in instances[(zone, gpu_type, num_gpus)]:
            instance_id = instance[0]
            if instance_id is not None:
                delete_spot_instance(zone, instance_id)

    logs2[datetime.now().strftime('%Y-%m-%dT%H:%M:%S.000Z')] = [None, 0]
    persist_dict()
    sys.exit(0)


def launch_spot_instance(zone, gpu_type, num_gpus, sir_id):
    instance_type = instance_types[(gpu_type, num_gpus)]
    with open("specification.json.template", 'r') as f1, open("specification.json", 'w') as f2:
        template = f1.read()
        specification_file = template % (instance_type, zone)
        f2.write(specification_file)
    command = """aws ec2 request-spot-instances --instance-count 1 --type persistent --launch-specification file://specification.json"""
    try:
        if sir_id is None:
            print("[%s] Trying to create instance with %d GPU(s) of type %s in zone %s" % (
                datetime.now().strftime('%Y-%m-%dT%H:%M:%S.000Z'), num_gpus, gpu_type, zone), file=sys.stderr)
            output = subprocess.check_output(command, shell=True).decode()
            return_obj = json.loads(output)
            sir_id = return_obj["SpotInstanceRequests"][0]["SpotInstanceRequestId"]
          #  time.sleep(60)

        command = """aws ec2 describe-spot-instance-requests --spot-instance-request-id %s""" % (
            sir_id)
        time.sleep(30)
        output = subprocess.check_output(command, shell=True).decode()

        if "InvalidSpotInstanceRequestID" in output or "canceled before it was fulfilled" in output:
            print("[%s] Sir request bad, trying to create instance with %d GPU(s) of type %s in zone %s" % (datetime.now().strftime('%Y-%m-%dT%H:%M:%S.000Z'), num_gpus, gpu_type, zone), file=sys.stderr)
            command = """aws ec2 request-spot-instances --instance-count 1 --type persistent --launch-specification file://specification.json"""
            output = subprocess.check_output(command, shell=True).decode()
            return_obj = json.loads(output)
            sir_id = return_obj["SpotInstanceRequests"][0]["SpotInstanceRequestId"]
          #  time.sleep(60)

            command = """aws ec2 describe-spot-instance-requests --spot-instance-request-id %s""" % (
                sir_id)
            time.sleep(30)
            output = subprocess.check_output(command, shell=True).decode()

        return_obj = json.loads(output)
        instance_id = return_obj["SpotInstanceRequests"][0]["InstanceId"]
        print(instance_id)
        aws_time = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.000Z')
        print("[%s] Created instance %s with %d GPU(s) of type %s in zone %s" % (aws_time,
            instance_id, num_gpus, gpu_type, zone))

        logs[instance_id] = [(gpu_type, num_gpus), aws_time, -1] # [instance, start time, end time]
        logs2[aws_time] = [instance_id, 1] # [instance id, running]
        persist_dict()
        print(logs)
        return [sir_id, instance_id, True]
    except Exception as e:
        print(e)
        pass
    #if spot_instance_request_id is not None:
    #    command = """aws ec2 cancel-spot-instance-requests --spot-instance-request-ids %s""" % (
    #        spot_instance_request_id)
    #    subprocess.check_output(command, shell=True)
    #print("[%s] Instance with %d GPU(s) of type %s creation failed" % (
    #    datetime.now().strftime('%Y-%m-%dT%H:%M:%S.000Z'), num_gpus, gpu_type))

    return [sir_id, None, False]

def monitor_spot_instance(zone, instance_id):
    command = """aws ec2 describe-instances --instance-id %(instance_id)s""" % {
        "instance_id": instance_id,
    }
    try:
        output = subprocess.check_output(command, shell=True).decode()
        if "running" in output:
            print("[%s] Instance %s running in zone %s" % (
                datetime.now().strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                instance_id, zone))
            return True
    except Exception as e:
        pass
    aws_time = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.000Z')
    print("[%s] Instance %s not running in zone %s" % (aws_time, instance_id, zone))
   
    if instance_id in logs: 
        logs[instance_id][-1] = aws_time
        logs2[aws_time] = [instance_id, -1]  # [instance id, not running]
        persist_dict()

    print(logs)
    
    # Delete spot instance in case it exists.
    delete_spot_instance(zone, None, instance_id)
    return False

def delete_spot_instance(zone, sir_id, instance_id):

    if sir_id is not None:

        command = """aws ec2 cancel-spot-instance-requests --spot-instance-request-ids %s""" % (
        sir_id)
        try:
            subprocess.check_output(command, shell=True)
            print("[%s] Successfully deleted spot instance request id %s" % (
                datetime.now().strftime('%Y-%m-%dT%H:%M:%S.000Z'), sir_id))
        except:
            return

    if instance_id is not None:
        command = """aws ec2 terminate-instances --instance-ids %(instance_id)s""" % {
            "instance_id": instance_id,
        }
        try:
            output = subprocess.check_output(command, shell=True)
            print("[%s] Successfully deleted instance %s" % (
                datetime.now().strftime('%Y-%m-%dT%H:%M:%S.000Z'), instance_id))
        except:
            return

def main(args):

    work_dir = args.zone
    zone = args.zone

    exists = os.path.isdir(work_dir)

    if not exists:
        os.mkdir(work_dir)

    copy('specification.json.template', work_dir + os.path.sep)
    os.chdir(work_dir)

    global instances
    for gpu_type in args.gpu_types:
        for num_gpus in args.all_num_gpus:
            if (gpu_type, num_gpus) not in instance_types:
                continue

            instance = [None, None, False]  # sir id, instance id, is created
            instances[(zone, gpu_type, num_gpus)] = [instance] * MAX_INSTANCES

    print(instances)

    logs2[datetime.now().strftime('%Y-%m-%dT%H:%M:%S.000Z')] = [None, 0]

    while True:
        # Spin in a loop; try to launch spot instances of particular type if
        # not running already. Check on status of instances, and update to
        # "not running" as needed.
        for (zone, gpu_type, num_gpus) in instances:
            i = 0
            for instance in instances[(zone, gpu_type, num_gpus)]:
                sir_id, instance_id, running = instance[0], instance[1], instance[2]
                if instance_id is not None:
                    running = \
                        monitor_spot_instance(zone, instance_id)
                if not running:
                    [sir_id, instance_id, running] = \
                        launch_spot_instance(zone, gpu_type, num_gpus, sir_id)
                instances[(zone, gpu_type, num_gpus)][i] = [sir_id, instance_id, running]
                i += 1

        time.sleep(10)
        print("Trying again")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
                description='Get AWS spot instance availability')
    parser.add_argument('--zone', type=str,
                        default=["us-east-1a"],
                        help='AWS availability zones')
    parser.add_argument('--gpu_types', type=str, nargs='+',
                        default=["v100", "k80"],
                        help='GPU types')
    parser.add_argument('--all_num_gpus', type=int, nargs='+',
                        default=[1, 4, 8, 16],
                        help='Number of GPUs per instance')
    args = parser.parse_args()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler2)
    main(args)
