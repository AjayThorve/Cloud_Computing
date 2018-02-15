## Author Ajay Thorve
### Subject: Cloud Computing
## netid: aat414
## N13008057

import sys
import boto3

# Terminate specific instance
def terminate_instance():
    ec2 = boto3.resource('ec2')
    for instance_id_i in sys.argv[1:]:
        instance = ec2.Instance(instance_id_i)
        response = instance.terminate()
        print("shutting down instance..termination in progress")
        instance.wait_until_terminated()
        print("\nInstance Terminated:\n",response)

# List all instances
def list_instances():
    ec2 = boto3.resource('ec2')
    for instance in ec2.instances.all():
        print("\nInstance ID : ",instance.id, "\nState : ", instance.state,"\nLocation : ", instance.placement['AvailabilityZone'], "\nIP : ", instance.public_ip_address)

if __name__ == '__main__':
    terminate_instance()
    list_instances()