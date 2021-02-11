# vmware-sd-wan-vco-vce-in-aws-with-python
Simple python script that leverages vmware sd-wan orchestrator rest api and aws boto3 to deploy a virtual edge in AWS.

Very simple script that leverages VMware SD-WAN Orchestrator API and AWS SDK for python.
It provisions a new profile and a new virtual vmware sd-wan edge (VCE) in the VMware SD-WAN #Orchestrator (VCO)

It will change the edge device settings shown below to be compatible with the cloudformation  template
vlan1 ip, ge2 as routed with public auto overlay, and ge3 routed with no overlay)

After provisioning the VCE, the script builds a green field cf template, populates its parameters
and launch a AWS cloudformation stack.

Original template can be found here:
https://vdc-download.vmware.com/sampleExchange/v1/downloads/6444
author: David Wight

Pre-requisites:

VMware SD-WAN:
 Orchestrator Target
 Enterprise admin account
 Enterprise user and user VCO API token
 
 AWS:
 Amazon Web Services (AWS) CLI credentials
 Python Modules:
 os, sys, requests, json , boto3 (AWS SDK for Python)

 more information about what is being built can be found here:
 https://docs.vmware.com/en/VMware-SD-WAN/4.2/sd-wan-aws-virtual-edge-deployment-guide/GUID-805915BF-C3D1-4B6D-A62F-859314A64896.html
 Not to be considered as best practices in using VMware VCO API
 Meant to be used in Lab environments - Please test it and use at your own risk

 please note that there's no guarantee or support from both author and VMware for this samples
 It is provided - AS IS - i.e. while we are glad to answer questions about API usage
 and behavior generally speaking, VMware cannot and do not specifically support these scripts

 Compatible with api v1 of the vmware sd-wan vco api
 using tokens to authenticate 
