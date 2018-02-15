## Author Ajay Thorve
### Subject: Cloud Computing
## netid: aat414
## N13008057

import sys
import boto3
import os
req_module_present = False
try:
    import requests
except ImportError:
    print("please install 'requests' module in python3 to create security group for the aws machine using your ip address, default security group would be used instead, and you wont be able to ssh into your linux instance")
else:
    req_module_present = True

# List all instances
def list_all_instances():
    print("listing all instances")
    ec2 = boto3.resource('ec2')
    for instance in ec2.instances.all():
        print("\nInstance ID : ",instance.id, 
            "\nState : ", instance.state,
            "\nLocation : ", instance.placement['AvailabilityZone'], 
            "\nIP : ", instance.public_ip_address)

# List specific instances
def list_instances(instance_id):
    print("listing recently created instance with id", instance_id)
    ec2 = boto3.resource('ec2')
    for instance in ec2.instances.all():
        if instance.id == instance_id:
            print("\nInstance ID : ",instance.id, 
                  "\nState : ", instance.state,
                  "\nLocation : ", instance.placement['AvailabilityZone'], 
                  "\nIP : ", instance.public_ip_address)

# Create new instance
def create_instance(sec_group_id,keyname):
    print("Now creating instance")
    try:
        ec2 = boto3.resource('ec2')
        instances = ec2.create_instances(ImageId='ami-f63b1193', 
                                        MinCount=1, 
                                        MaxCount=1, 
                                        InstanceType='t2.micro', 
                                        KeyName = str(keyname),
                                        SecurityGroupIds = [sec_group_id])
        instance = instances[0]
        print("\nNew Instance Created\nInstance ID : ",instance.id)
    except:
        print("something went wrong...exiting program\n more details:",sys.exc_info())
        sys.exit()
    print("successfully created new instance")
    print("waiting for instance status to change to running from pending...")
    instance.wait_until_running()
    #reload the instance attributes
    instance.load()
    print("instance is running now!!!")
    print("dns",instance.public_dns_name)
    return (instance.id, instance.public_dns_name)

#create key
def create_key(keyname):
    print("creating new key-pair for the instance...")
    if check_key_pair_exists(keyname):
        return str(keyname)
    try:
        ec2 = boto3.resource('ec2')
        filename= str(str(keyname)+'.pem')
        #to make sure file does not exists locally
        try:
            os.remove(filename)
        except OSError:
            pass
        outfile = open(filename,'w')
        key_pair = ec2.create_key_pair(KeyName=str(keyname))
        KeyPairOut = str(key_pair.key_material)
        outfile.write(KeyPairOut)
        os.chmod(filename, 0o400)
    except:
        print("something went wrong\n more details:",sys.exc_info())
    else:
        print("key created successfully: "+str(keyname)+".pem")
    return str(keyname)
        
#check if key-pair already exists in aws
def check_key_pair_exists(keyname):
    ec2_client = boto3.client('ec2')
    try:
        desc_key_pair = ec2_client.describe_key_pairs(KeyNames=[keyname])
    except:
        return False
    else:
        if(len(desc_key_pair)>0):
            print("key pair named",keyname,"already exists, using the same")
            return True
        else:
            return False
#check if security group already exists
def check_sec_group_exists(group_name):
    ec2_client = boto3.client("ec2")
    try:
        desc_sec_groups = ec2_client.describe_security_groups(GroupNames=[group_name])
    except:
        return (ec2_client,False)
    else:
        if(len(desc_sec_groups)>0):
            print("security group already exists", desc_sec_groups['SecurityGroups'][0]['GroupId'])
            return (ec2_client,desc_sec_groups['SecurityGroups'][0]['GroupId'])
        else:
            return (ec2_client,False)

#create security group
def create_security_group():
    #to avoid group already exists error, delete already existing security group with same name
    ec2_client,group_id = check_sec_group_exists('Cloud_aat414')
    
    if group_id:
        return group_id;
    
    #else do the following: create new sec group, and ingress rules for ssh, and return group id
    response = ec2_client.create_security_group(
        Description='Cloud_aat414 for ssh only',
        GroupName='Cloud_aat414',
    )
    sg_id = response['GroupId']
    sg_desc = "Cloud_aat414 for ssh only"

    old_ip = "127.0.0.1"
    current_ip = requests.get('http://ip.42.pl/raw').text
    try:
        ec2 = boto3.resource("ec2")
        security_group = ec2.SecurityGroup(sg_id)

        for p in security_group.ip_permissions:
            for r in p['IpRanges']:
                if 'Description' in r and r['Description'] == sg_desc:
                    old_ip = r['CidrIp']
                    print("found old IP :",old_ip)
                else:
                    print("can't find old IP")

        if old_ip != "127.0.0.1":
            security_group.revoke_ingress(IpProtocol="tcp", CidrIp=old_ip, FromPort=22, ToPort=22)
            print("remove of old IP",old_ip)

        perms = {
            'IpProtocol': "tcp",
            'FromPort': 22,
            'ToPort': 22,
            'IpRanges': [{'CidrIp': current_ip+"/32", 'Description': sg_desc}]
        }  
        security_group.authorize_ingress(IpPermissions=[perms])
        print("updated with "+ current_ip +"/32")
    except:
        print("security group function: something went wrong...\n more details",sys.exc_info()[0])
        print("exiting program") 
        sys.exit()
    print("security group successfully created with id:",sg_id)
    return sg_id

#main execution
if __name__ == '__main__':
    #list all instances 
    list_all_instances()
    
    #create a key-pair for the aws instnace
    keyname = create_key('ec2-aat414_cloud')

    #checking if python's request module is present to extract current 
    # machine's public ip address to assign to security groups, else a default security group would be assigned
    if req_module_present:
        sec_group_id = create_security_group()
    else:
        sec_group_id = 'default'

    #create instance
    instance_id,instance_dns_name = create_instance(sec_group_id,keyname)
    
    #list the recently created instance
    list_instances(instance_id)
    
    print("you can successfully ssh into the instance as per the security group",sec_group_id)
    print("ssh -i "+str(keyname)+".pem ec2-user@"+str(instance_dns_name))
    print("please use the following command to terminate the instance after you are done using the instance(very important)")
    print("python3 terminate_instances.py "+str(instance_id))
