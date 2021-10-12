#!/usr/bin/env python3
#
# Author: vfrancadesou@vmware.com

# Very simple script that leverages VMware SD-WAN Orchestrator API and AWS SDK for python.
# It provisions a new profile and a new virtual vmware sd-wan edge (VCE) in the VMware SD-WAN #Orchestrator (VCO)

# It will change the edge device settings shown below to be compatible with the cloudformation  template
# :vlan1 ip, ge2 as routed with public auto overlay, and ge3 routed with no overlay)

# After provisioning the VCE, the script builds a green field cf template, populates its parameters
# and launch a AWS cloudformation stack.

# Original template can be found here:
# https://vdc-download.vmware.com/sampleExchange/v1/downloads/6444
# author: David Wight

# Pre-requisites:

# VMware SD-WAN:
# Orchestrator Target
# Enterprise admin account
# Enterprise user and user VCO API token
# AWS:
# Amazon Web Services (AWS) CLI credentials
# Python Modules:
# os, sys, requests, json , boto3 (AWS SDK for Python)

# more information about what is being built can be found here:
# https://docs.vmware.com/en/VMware-SD-WAN/4.2/sd-wan-aws-virtual-edge-deployment-guide/GUID-805915BF-C3D1-4B6D-A62F-859314A64896.html

# Not to be considered as best practices in using VMware VCO API
# Meant to be used in Lab environments - Please test it and use at your own risk
#
# please note that VMWare API and Support team - do not guarantee this samples
# It is provided - AS IS - i.e. while we are glad to answer questions about API usage
# and behavior generally speaking, VMware cannot and do not specifically support these scripts
#
# Compatible with api v1 of the vmware sd-wan vco api
# using tokens to authenticate

import os
import sys
import requests
import json
import random
import argparse
import boto3
from copy import deepcopy

######### VELO VARIABLES AND FUNCTIONS

########## VCO info and credentials
# Prefer to use OS environments to hold token variable
token = os.environ['VCO_TOKEN']
VCO_FQDN=os.environ['VCO_HOSTNAME']
vco_url = 'https://' + os.environ['VCO_HOSTNAME'] + '/portal/rest/'
headers = {"Content-Type": "application/json", "Authorization": token}
ProfileName='AWS HUB Profile'
EdgeName='AWS-VCE-'+str(random.randint(1,10000))
EdgeContactName='Vladimir'
EdgeContactEmail='vfrancadesou-aws@vmware.com'

### EDGE contact information
site={
      "contactName": EdgeContactName,
      "contactEmail": EdgeContactEmail,
            "streetAddress": None,
      "streetAddress2": None,
      "city": None,
      "state": None,
      "postalCode": None,
      "country": None,
      "lat": None,
      "lon": None,
      "timezone": None,
      "locale": None,
      "shippingSameAsLocation": 1,
      "shippingContactName": None,
      "shippingAddress": None,
      "shippingAddress2": None,
      "shippingCity": None,
      "shippingState": None,
      "shippingPostalCode": None,
      "shippingCountry": None,
       "modified": None
    }

###
######## VCO API methods
get_enterprise = vco_url + 'enterprise/getEnterprise'
get_edgelist = vco_url+'enterprise/getEnterpriseEdgeList'
get_edgeconfig = vco_url + 'edge/getEdgeConfigurationStack'
update_edgeconfig = vco_url+'configuration/updateConfigurationModule'
edge_prov = vco_url+'edge/edgeProvision'
get_profiles =vco_url + 'enterprise/getEnterpriseConfigurationsPolicies'
create_profile = vco_url+'configuration/cloneEnterpriseTemplate'

######## AWS variable and inputs
#aws ec2 keypair name
KeyName='AWS-KEY-CALI' ### must already exist
BucketName='vm-velocf'
File2Upload='new-velo-cf.json'
StackName='VELO-STACK'+str(random.randint(1,1000))
CfRegion = 'us-west-1' ### if CFRegion is different make sure to change region in velocf below as well
### To run or not to run the AWS stack
runaws=True

### modified AWS Cloud Formation GREEN  FIELD TEMPLATE
velocf={
 "AWSTemplateFormatVersion": "2010-09-09",
 "Mappings" : {
    "RegionMap" : {
      "us-east-2" : {"322" : "ami-0667712c0cc7ccbd6", "331" : "ami-00009cd364607db91"},
      "us-east-1" : {"322" : "ami-02d53ee6e90715a83", "331" : "ami-0a9373a4b23e149b7"},
      "us-west-1" : {"322" : "ami-056b3e0e020d5733c", "331" : "ami-0eae7918e6c5e03e3"},
      "us-west-2" : {"322" : "ami-04d3e79314781094f", "331" : "ami-0e2374b672d5149c3"},
      "ap-south-1" : {"322" : "ami-0c74ea9d8c66c1a87", "331" : "ami-08df28503c779c65b"},
      "ap-northeast-2" : {"322" : "ami-0f7514d14209b90ff", "331" : "ami-001c1e312fec38b26"},
      "ap-southeast-1" : {"322" : "ami-0d0e6c10cf0ffd3a9", "331" : "ami-00b0ac7201061dce6"},
      "ap-southeast-2" : {"322" : "ami-09672eaa998504af3", "331" : "ami-0b7196fd587231352"},
      "ap-northeast-1" : {"322" : "ami-05eb836595f666ab3", "331" : "ami-02028fdfda2bedef3"},
      "ca-central-1" : {"322" : "ami-0cb42e3a9a6adaf09", "331" : "ami-03a3ed427dd6af221" },
      "eu-central-1" : {"322" : "ami-0d2f8031303625653", "331" : "ami-0e3ef4a959a447466"},
      "eu-west-1" : {"322" : "ami-0967d4240a3fb5742", "331" : "ami-0f5a1ddf49df24d29"},
      "eu-west-2" : {"322" : "ami-0e9836eb5505034b6", "331" : "ami-0910c04a99eda46f3"},
      "eu-west-3" : {"322" : "ami-055c7e693f0504309", "331" : "ami-00bb1d7d48dd45aac"},
      "eu-north-1" : {"322" : "ami-1aed6564", "331" : "ami-ba9c16c4"},
      "sa-east-1" : {"322" : "ami-092fa003ace20ca2b", "331" : "ami-03476bb22664d682d"},
      "us-gov-east-1" : {"322" : "ami-9b31d0ea", "331" : "ami-b87191c9"},
      "us-gov-west-1" : {"322" : "ami-3b11605a", "331" : "ami-f3d08492"}
    }
  },
 "Parameters": {
    "SoftwareVersion": {
      "Description": "VeloCloud Virtual Edge Software Version",
      "Type": "String",
      "Default": "331",
      "AllowedValues": ["322", "331"],
      "ConstraintDescription": "Must be one of the following: 322, or 331"
    },
    "EC2InstanceType": {
      "Description": "Throughput and number of NICs dictate instance type",
      "Type": "String",
      "Default": "c4.xlarge",
      "AllowedValues": [
        "c4.large", "c4.xlarge", "c4.2xlarge", "c4.4xlarge",
        "c5.large", "c5.xlarge", "c5.2xlarge", "c5.4xlarge"
      ]
    },
    "ResourcePrefix" : {
     "Description" : "Prefix used for naming all resources created by this template",
     "Type" : "String",
     "Default" : "velocloud"
    },
    "AvailabilityZone" : {
      "Description" : "Availability zone to deploy in",
      "Type" : "String",
      "Default" : "us-west-1b" ### CHANGE AS NEEDED
    },
    "VeloCloudEdgeName" : {
      "Description" : "Name of Edge to be deployed",
      "Type" : "String",
      "Default" : "VVCE"
   },
   "ActivationKey" : {
     "Description" : "Edge Activation Key",
     "Type" : "String",
     "AllowedPattern": "^[A-Z0-9-]+$",
     "Default" : "AAAA-BBBB-CCCC-DDDD"
   },
   "IgnoreCertificateValidation" : {
     "Description" : "Set to true if using private or self signed certificate on the VCO",
     "Type" : "String",
     "Default" : "false",
     "AllowedValues" : ["true", "false"]
   },
   "VCO" : {
     "Description" : "Orchestrator IP address or hostname (fqdn)",
     "Type" : "String",
     "Default" : "vco58-usvi1.velocloud.net"
   },
   "VpcCidrBlockValue" : {
     "Description" : "CIDR block for the VPC",
     "Type" : "String",
     "Default" : "10.6.0.0/16"
   },
   "PrivateCidrBlockValue" : {
     "Description" : "CIDR block for the LAN side of the Edge",
     "Type" : "String",
     "Default" : "10.6.1.0/24"
   },
   "PublicCidrBlockValue" : {
     "Description" : "CIDR block for the WAN side of the Edge",
     "Type" : "String",
     "Default" : "10.6.0.0/24"
   },
   "VeloCloudKeyPairName" : {
     "Description" : "Public/Private Key Name of Edge to be deployed",
     "Type" : "AWS::EC2::KeyPair::KeyName",
     "Default" : "AWS-VIRG-KEY"
   }
 },
 "Resources": {
   "VelocloudVPC": {
     "Type": "AWS::EC2::VPC",
     "Properties": {
       "CidrBlock": { "Ref": "VpcCidrBlockValue" },
       "Tags": [ { "Key": "Name", "Value": { "Fn::Join": [ "-", [ { "Ref" : "ResourcePrefix" }, "VPC"] ] } } ]
     }
   },
   "PublicCidrBlock": {
     "Type": "AWS::EC2::Subnet",
     "Properties": {
       "CidrBlock": { "Ref": "PublicCidrBlockValue" },
       "AvailabilityZone": { "Ref": "AvailabilityZone" },
       "VpcId": { "Ref": "VelocloudVPC" },
       "Tags": [ { "Key": "Name", "Value": { "Fn::Join": [ "-", [ { "Ref" : "ResourcePrefix" }, "Public-SN"] ] } } ]
     }
   },
   "PrivateCidrBlock": {
     "Type": "AWS::EC2::Subnet",
     "Properties": {
       "CidrBlock": { "Ref": "PrivateCidrBlockValue" },
       "AvailabilityZone": { "Ref": "AvailabilityZone" },
       "VpcId": { "Ref": "VelocloudVPC" },
       "Tags": [ { "Key": "Name", "Value": { "Fn::Join": [ "-", [ { "Ref" : "ResourcePrefix" }, "Private-SN"] ] } } ]
     }
   },
   "InternetGateway": {
     "Type": "AWS::EC2::InternetGateway",
     "Properties": {
       "Tags": [ { "Key": "Name", "Value": { "Fn::Join": [ "-", [ { "Ref" : "ResourcePrefix" }, "IGW"] ] } } ]
     }
   },
   "PrivateRouteTable": {
     "Type": "AWS::EC2::RouteTable",
     "Properties": {
       "VpcId": { "Ref": "VelocloudVPC" },
       "Tags": [ { "Key": "Name", "Value": { "Fn::Join": [ "-", [ { "Ref" : "ResourcePrefix" }, "Private-RT"] ] } } ]
     }
   },
   "PublicRouteTable": {
     "Type": "AWS::EC2::RouteTable",
     "Properties": {
       "VpcId": { "Ref": "VelocloudVPC" },
       "Tags": [ { "Key": "Name", "Value": { "Fn::Join": [ "-", [ { "Ref" : "ResourcePrefix" }, "Public-RT"] ] } } ]
     }
   },
   "PublicIpAddress": {
     "Type": "AWS::EC2::EIP",
     "DependsOn": [ "VpcGatewayAttachment" ],
     "Properties": {
      "Domain": "vpc"
     }
   },
   "VceInterfaceGe1": {
     "Type": "AWS::EC2::NetworkInterface",
     "Properties": {
       "Description": "Management Interface",
       "SourceDestCheck": "false",
       "SubnetId": { "Ref": "PublicCidrBlock" },
       "GroupSet": [ { "Ref": "VelocloudWANSecurityGroup" } ]
     }
   },
   "VceInterfaceGe2": {
     "Type": "AWS::EC2::NetworkInterface",
     "Properties": {
       "Description": "WAN Interface",
       "SourceDestCheck": "false",
       "SubnetId": { "Ref": "PublicCidrBlock" },
       "GroupSet": [ { "Ref": "VelocloudWANSecurityGroup" } ]
     }
   },
   "VceInterfaceGe3": {
     "Type": "AWS::EC2::NetworkInterface",
     "Properties": {
       "Description": "LAN Interface",
       "SourceDestCheck": "false",
       "SubnetId": { "Ref": "PrivateCidrBlock" },
       "GroupSet": [ { "Ref": "VelocloudLANSecurityGroup" } ]
     }
   },
   "VeloCloudEdge": {
     "Type": "AWS::EC2::Instance",
     "Properties": {
       "ImageId": { "Fn::FindInMap" : [ "RegionMap", { "Ref" : "AWS::Region" }, { "Ref": "SoftwareVersion" }] },
       "InstanceType": { "Ref" : "EC2InstanceType" },
       "KeyName": {"Ref": "VeloCloudKeyPairName"},
       "Tags": [
         { "Key": "Name", "Value": { "Ref" : "VeloCloudEdgeName" } },
         { "Key": "Owner", "Value": "Generated with VeloClouds Greenfield CloudFormation Template" }
       ],
       "UserData" : { "Fn::Base64" : { "Fn::Join" : ["", [
         "#cloud-config\n",
         "velocloud:\n",
         "  vce:\n",
         "    vco: ", { "Ref": "VCO" }, "\n",
         "    activation_code: ", { "Ref": "ActivationKey" }, "\n",
         "    vco_ignore_cert_errors: ", { "Ref": "IgnoreCertificateValidation" }, "\n"
       ]]}},
       "NetworkInterfaces": [
         {
           "DeleteOnTermination": "false",
           "NetworkInterfaceId":  { "Ref": "VceInterfaceGe1"},
           "DeviceIndex": 0
         },
         {
           "DeleteOnTermination": "false",
           "NetworkInterfaceId":  { "Ref": "VceInterfaceGe2"},
           "DeviceIndex": 1
         },
         {
           "DeleteOnTermination": "false",
           "NetworkInterfaceId":  { "Ref": "VceInterfaceGe3"},
           "DeviceIndex": 2
         }
       ]
     }
   },
   "VpcGatewayAttachment": {
     "Type": "AWS::EC2::VPCGatewayAttachment",
     "Properties": {
       "VpcId": { "Ref": "VelocloudVPC" },
       "InternetGatewayId": { "Ref": "InternetGateway" }
     },
     "DependsOn": [ "InternetGateway" ]
   },
   "PublicRouteTableAssociation": {
     "Type": "AWS::EC2::SubnetRouteTableAssociation",
     "Properties": {
       "RouteTableId": { "Ref": "PublicRouteTable" },
       "SubnetId": { "Ref": "PublicCidrBlock" }
     }
   },
   "PrivateRouteTableAssociation": {
     "Type": "AWS::EC2::SubnetRouteTableAssociation",
     "Properties": {
       "RouteTableId": { "Ref": "PrivateRouteTable" },
       "SubnetId": { "Ref": "PrivateCidrBlock" }
     }
   },
   "PublicDefaultRoute": {
     "Type": "AWS::EC2::Route",
     "Properties": {
       "DestinationCidrBlock": "0.0.0.0/0",
       "RouteTableId": { "Ref": "PublicRouteTable" },
       "GatewayId": { "Ref": "InternetGateway" }
     },
     "DependsOn": [ "InternetGateway", "VpcGatewayAttachment", "PublicRouteTable" ]
   },
   "PrivateDefaultRoute": {
     "Type": "AWS::EC2::Route",
     "Properties": {
       "DestinationCidrBlock": "0.0.0.0/0",
       "RouteTableId": { "Ref": "PrivateRouteTable" },
       "NetworkInterfaceId": { "Ref": "VceInterfaceGe3" }
     },
     "DependsOn": [ "VceInterfaceGe3", "PrivateRouteTable" ]
   },
   "ElasticIpAssociation": {
     "Type": "AWS::EC2::EIPAssociation",
     "Properties": {
       "AllocationId": { "Fn::GetAtt": ["PublicIpAddress", "AllocationId"] },
       "NetworkInterfaceId": { "Ref": "VceInterfaceGe2" }
     }
   },
   "VelocloudWANSecurityGroup": {
     "Type": "AWS::EC2::SecurityGroup",
     "Properties": {
       "GroupDescription": "WAN Facing Security Group",
       "VpcId": { "Ref": "VelocloudVPC" },
       "Tags": [ { "Key": "Name", "Value": { "Fn::Join": [ "-", [ { "Ref" : "ResourcePrefix" }, "WAN-SG"] ] } } ]
     }
   },
   "AllowSNMP": {
     "Type": "AWS::EC2::SecurityGroupIngress",
     "Properties": {
       "GroupId": { "Ref": "VelocloudWANSecurityGroup" },
       "IpProtocol": "udp",
       "FromPort": "161",
       "ToPort": "161",
       "CidrIp": "0.0.0.0/0"
     }
   },
   "AllowSSH": {
     "Type": "AWS::EC2::SecurityGroupIngress",
     "Properties": {
       "GroupId": { "Ref": "VelocloudWANSecurityGroup" },
       "IpProtocol": "tcp",
       "FromPort": "22",
       "ToPort": "22",
       "CidrIp": "0.0.0.0/0"
     }
   },
   "AllowVCMP": {
     "Type": "AWS::EC2::SecurityGroupIngress",
     "Properties": {
       "GroupId": { "Ref": "VelocloudWANSecurityGroup" },
       "IpProtocol": "udp",
       "FromPort": "2426",
       "ToPort": "2426",
       "CidrIp": "0.0.0.0/0"
     }
   },
   "VelocloudLANSecurityGroup": {
     "Type": "AWS::EC2::SecurityGroup",
     "Properties": {
       "GroupDescription": "LAN Facing Security Group - WARNING: Default is Allow ALL, adjust accordingly your security needs",
       "VpcId": { "Ref": "VelocloudVPC" },
       "Tags": [ { "Key": "Name", "Value": { "Fn::Join": [ "-", [ { "Ref" : "ResourcePrefix" }, "LAN-SG"] ] } } ]
     }
   },
   "AllowLANTraffic": {
     "Type": "AWS::EC2::SecurityGroupIngress",
     "Properties": {
       "GroupId": { "Ref": "VelocloudLANSecurityGroup" },
       "IpProtocol": "-1",
       "FromPort": "-1",
       "ToPort": "-1",
       "CidrIp": "0.0.0.0/0"
     }
   }
 },
 "Description": "VMware SD-WAN by VeloCloud CloudFormation Template (2021) - modified by vfrancadesou@vmware.com"
}


########
######## VCO FUNCTIONS
#######

#### RETRIEVE ENTERPRISE ID for this user
def find_velo_enterpriseId():
	#Fetch enterprise id convert to JSON
	eid=0
	try:
         #print(headers)
         enterprise = requests.post(get_enterprise, headers=headers, data='')

	except Exception as e:
	   print('Error while retrivieng Enterprise')
	   print(e)
	   sys.exit()
	ent_j = enterprise.json()
	eid=ent_j['id']
	print('Enterprise Id = %d'%(eid))
	return eid

#### CREATE NEW VMWARE SD-WAN CONFIGURATION PROFILE

def create_velo_profile(eid,ProfileName):
### Confirm existing profile names, if "AWS-PROFILE" not found, create a new profile
 params = {	}
 try:
         profile = requests.post(get_profiles, headers=headers, data=json.dumps(params))
 except Exception as e:
	   print('error getting profiles')
	   print(e)
	   sys.exit()
 prof_dict = profile.json()
 #print(prof_dict)
 length = len(prof_dict)
 z=0
 ProfId=0
 notfound=True
 pid=0
 while z < length:
        if(ProfileName==prof_dict[z]['name']):
                 pid = prof_dict[z]['id']
                 print ('Profile named '+ProfileName+' already found on VCO '+VCO_FQDN+' with Profile id: '+str(pid))
                 notfound=False
                 return pid
        z+=1
 if(notfound):
		#Provision new Profile and grab its id
		 params = {"id" : eid,"name":ProfileName}
		 print('Profile not found, creating new one')
		 profile_resp = requests.post(create_profile, headers=headers, data=json.dumps(params))
		 #print(profile_resp.json())
		 prof_dict = profile_resp.json()
		 pid = prof_dict['id']
		 print('New Profile named '+ProfileName+' created with Id = %d'%(pid))
		 return pid

#### PROVISION NEW VMWARE SD-WAN EDGE
def provision_velo_edge(eid,pid,EdgeName,site):
	#### Provision new virtual edge in the AWS Profile
	#Provision new Profile and grab its id
	rEdgeName=EdgeName
	params = {'id' : eid,'name':rEdgeName,'modelNumber': 'virtual','configurationId': pid,'site': site}
	try:
		edid = requests.post(edge_prov, headers=headers, data=json.dumps(params))
		edid_j = edid.json()
		edid=edid_j['id']
		activationkey=edid_j['activationKey']
		print('New Edge named '+rEdgeName+' created with Id '+str(edid)+' and activation key '+activationkey)
		return [edid,activationkey]

	except Exception as e:
	     print(e)
	     sys.exit()

def change_edge_config(eid,edid):
    ### Grab Edge Device Settings
    params = {'edgeId': edid}
    respj = requests.post(get_edgeconfig, headers=headers, data=json.dumps(params))
    resp=respj.json()
    edgeSpecificProfile = dict(resp[0])
    edgeSpecificProfileDeviceSettings = [m for m in edgeSpecificProfile['modules'] if m['name'] == 'deviceSettings'][0]
    edgeSpecificProfileDeviceSettingsData = edgeSpecificProfileDeviceSettings['data']
    moduleId = edgeSpecificProfileDeviceSettings['id']
    ### Adding an IP on Vlan 1
    edgeSpecificProfileDeviceSettingsData['lan']['networks'][0]['cidrIp'] = '127.0.0.10'
    edgeSpecificProfileDeviceSettingsData['lan']['networks'][0]['advertise'] = False
    edgeSpecificProfileDeviceSettingsData['lan']['networks'][0]['cidrPrefix'] = '30'
    edgeSpecificProfileDeviceSettingsData['lan']['networks'][0]['netmask'] = '255.255.255.252'
    edgeSpecificProfileDeviceSettingsData['lan']['networks'][0]['dhcp']['enabled'] = False

    # Changing existing routed GE3 configuration
    routedInterfaces = edgeSpecificProfileDeviceSettingsData['routedInterfaces']
    for iface in routedInterfaces:
        if iface['name'] == 'GE3':
            iface['override'] = True
            iface['advertise'] = True
            iface['natDirect'] = False
            iface['wanOverlay'] = 'DISABLED'
    interface={"name":"GE"}
    routedInterfaces.insert(0,interface)
    routedInterfaces.insert(1,interface)
    routedInterfaces[0]=deepcopy(routedInterfaces[2])
    routedInterfaces[1]=deepcopy(routedInterfaces[2])
    routedInterfaces[0]['name'] = 'GE1'
    routedInterfaces[1]['name'] = 'GE2'
    for iface in routedInterfaces:
        if iface['name'] == 'GE2':
            iface['override'] = True
            iface['advertise'] = False
            iface['natDirect'] = True
            iface['wanOverlay'] = 'AUTO_DISCOVERED'

    edgeSpecificProfileDeviceSettingsData['routedInterfaces']=deepcopy(routedInterfaces)
    testResponse = {}
    testResponse['data'] = edgeSpecificProfileDeviceSettingsData
    ########### Change VCE device settings so it matches AWS cloudformation
    params3 = {
    "id" : moduleId,
    "returnData" : 'true',
    "_update":  testResponse,
    "name":"deviceSettings"}
    resp = requests.post(update_edgeconfig, headers=headers, data=(json.dumps(params3)))
    respo_j=resp.json()
    print('Devices Settings updated - these are needed for AWS deployment')

##############################   /////   #######################
####                          AWS FUNCTIONS
##############################   /////   #######################
############# Create S3 bucket and upload file to it
def upload_file_to_s3(bucketname,file2upload):
	# check if bucket alread exists if not create one and
	# upload new cloud formation template to S3 bucket named 'velocf'
	# make file public
	bucket_name=bucketname
	upload_file=file2upload
	found=False
	s3 = boto3.resource('s3')
	for bucket in s3.buckets.all():
		if (bucket_name==bucket.name):
			print('Bucket '+bucket.name+' Found')
			found=True
	if not found:
		print('Creating new S3 bucket - '+bucket_name)
		s3.create_bucket(Bucket=bucket_name)
	#upload file and make it public
	s3.Object(bucket_name, upload_file).put(Body=open(upload_file, 'rb'), ACL='public-read')
	s3FileUrl = "https://%s.s3.amazonaws.com/%s" % (bucket_name, upload_file)
	print('File URL = '+s3FileUrl)
	return s3FileUrl
############# Deploy CF Stack
def deploy_aws_cf_stack(stackname,awsregion,s3fileurl):
	cf_template_url=s3fileurl
	cf_region=awsregion
	#-- Connect to AWS region specified in parameters file
	print("Connecting to region: " + cf_region)
	lo_cf_client = boto3.client('cloudformation', cf_region)
	cf_stack_name = stackname
	#-- Check if this stack name already exists
	lo_stack_list = lo_cf_client.describe_stacks()["Stacks"]
	ll_stack_exists = False
	for lo_stack in lo_stack_list:
		if cf_stack_name == lo_stack["StackName"]:
			print("Stack " + cf_stack_name + " already exists.")
			ll_stack_exists = True
	#-- If  stack  exists, delete it first
	if ll_stack_exists:
		print(" Delete existing Stack  " + cf_stack_name)
		lo_cf_client.delete_stack(StackName=cf_stack_name)
	la_create_stack_parameters = []
	#-- Call CloudFormation API and create the stack
	print(" ")
	print("Creating Stack : " + cf_stack_name)
	cf_cur_status = ""
	apiresult = lo_cf_client.create_stack(StackName=cf_stack_name, DisableRollback=False, TemplateURL=cf_template_url, Parameters=la_create_stack_parameters, Capabilities=["CAPABILITY_IAM"])
	print("API result: ")
	print(apiresult)

######################### Main Program #####################
#### MAIN BODY
######################### Main Program #####################
######################### Main Program #####################
#### MAIN BODY
######################### Main Program #####################
def main():
        parser = argparse.ArgumentParser()
        parser.add_argument("-a", "--aws", action='store_true', help="Deploy CF stack in AWS",required=False)
#parser.add_argument('EdgeSource')
#parser.add_argument('EdgeDest')
#parser.add_argument('Map')
#print(f'Source 5x0 {args.EdgeSource} and Target 6x0 {args.EdgeDest} with Interface Mapping {args.EdgeSource}')

        args = parser.parse_args()
        eid = find_velo_enterpriseId()
        pid = create_velo_profile(eid,ProfileName)
        new_edge_l = provision_velo_edge(eid,pid,EdgeName,site)
        edid=new_edge_l[0]
        activationkey=new_edge_l[1]
        ### Change Edge Configuration so it can be used in AWS
        change_edge_config(eid,edid)
        #Populate new cloudformation file with all parameters needed
        # 2 options , read from file
        # Read template from file
        # with open(cf_file) as json_file:
        	#data = json.load(json_file)
        # or
        # Use template pre-inserted inside this python code
        data = velocf
        data['Parameters']['ActivationKey']['Default'] = activationkey
        data['Parameters']['VeloCloudKeyPairName']['Default']=KeyName
        data['Parameters']['VCO']['Default']=VCO_FQDN
        data['Parameters']['VeloCloudEdgeName']['Default']=EdgeName

        # Dumping the result in a json file so it can also be used manually or uploaded to AWS S3
        with open('new-velo-cf.json', 'w') as outfile:
        	outfile.write(json.dumps(data))

        ################ ////////////////// ##############################################
        # AWS PART:
        ################ ////////////////// ##############################################
        if(args.aws):
        	# Upload the pre-populate cf template to a S3 bucket
        	# Create the bucket if it does not already exists
        	s3url=upload_file_to_s3(BucketName,File2Upload)
        	# Deploy a new CloudFormation stack in AWS
        	deploy_aws_cf_stack(StackName,CfRegion,s3url)

if __name__ == "__main__":
    main()
