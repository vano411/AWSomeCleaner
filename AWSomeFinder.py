# Please ensure you THOROUGHLY read the README.md file before running this script.

from datetime import datetime
import boto3
import re
import sys
import time

################################################
# \/ \/ \/ CRITICAL CONTROL VARIABLES \/ \/ \/ #
################################################

print ("------------------------------------------------------------------------------")
print ("Welcome to AWSome Finder!")
print ()
print ("Let's gather some info first.")
print ("------------------------------------------------------------------------------")



regions = []
print ("Which region are we deploying this script to?")
print ()
print ("1. N. California  (us-west-1)")
print ("2. Oregon         (us-west-2)")
print ("3. N. Virginia    (us-east-1)")
print ("4. Ohio           (us-east-2)")
print ("5. Tokyo          (ap-northeast-1)")
print ("6. Ireland        (eu-west-1)")
print ("7. London         (eu-west-2)")
print ("8. Singapore      (ap-southeast-1)")
print ("9. Sydney         (ap-southeast-2)")
print ("10. Sao Paulo     (sa-east-1)")
print ("11. All Regions")
print ()

while len(regions) == 0:
  val2 = input("Select a region(s): ")

  if val2 == "1":
    regions = ['us-west-1']
  elif val2 == "2":
    regions = ['us-west-2']
  elif val2 == "3":
    regions = ['us-east-1']
  elif val2 == "4":
    regions = ['us-east-2']
  elif val2 == "5":
    regions = ['ap-northeast-1']
  elif val2 == "6":
    regions = ['eu-west-1']
  elif val2 == "7":
    regions = ['eu-west-2']
  elif val2 == "8":
    regions = ['ap-southeast-1']
  elif val2 == "9":
    regions = ['ap-southeast-2']
  elif val2 == "10":
    regions = ['sa-east-1']
  elif val2 == "11":
    regions = ['us-west-1', 'us-west-2', 'us-east-1', 'us-east-2', 'ap-northeast-1', 'eu-west-1', 'eu-west-2', 'ap-southeast-1', 'ap-southeast-2', 'sa-east-1']
  else:
    print ("Invalid input. Choose from the list above.")

print ("------------------------------------------------------------------------------")
print ()
print ("Input the maximum age of resources to keep in DAYS")
print ("e.g. 365 means all resources older than one year from today will be flagged for deletion")
print ()

while True:
  try:
    ec2delta = int(input("Enter the maximum age of EC2 instances to keep in DAYS: "))
    break
  except ValueError:
    print ("Enter numbers only.")

while True:
  try:
    amidelta = int(input("Enter the maximum age of AMI's to keep in DAYS: "))
    break
  except ValueError:
    print ("Enter numbers only.")

while True:
  try:
    snapdelta = int(input("Enter the maximum age of Snapshots to keep in DAYS: "))
    break
  except ValueError:
    print ("Enter numbers only.")

print ()

print ("------------------------------------------------------------------------------")
print ("Thank you! Please stand by while I generate a list of resources for you...")
print ()

################################################
# /\ /\ /\ CRITICAL CONTROL VARIABLES /\ /\ /\ #
################################################

# Redirect stdout to file
timestr = time.strftime("%Y%m%d-%H%M%S")
filename = "AWSomeResults-"+str(timestr)+".txt"
original_stdout = sys.stdout
sys.stdout = open(filename, 'w')


# Creating lists which will be populated
oldEC2 = []
protEC2 = []
oldAMI = []
oldAMIsnap = []
oldSnap = []
runInst = []
activeSnap = []
gb = []
nonhvmsnap = []

# Function which takes the creation date of an AWS resource and returns its age in days
def ageFinder(day):
    cdate1 = str(day)
    cdate2 = cdate1[0:10]
    date1 = datetime.strptime(cdate2, "%Y-%m-%d")
    date2 = datetime.now()
    diff = date2 - date1
    return diff.days

print ("-------------------------------------------------------------------------------")
print ("-------------------------- EC2's older than",ec2delta ,"days ---------------------------")
print ("-------------------------------------------------------------------------------")

# Gather a list of STOPPED instances older than the "ec2delta" variable
for region in regions:
  ec2 = boto3.resource('ec2',region_name=region)
  client = boto3.client('ec2', region_name=region)
  instances = ec2.instances.filter()

  for instance in instances:
    if instance.state['Name'] == "stopped": 
    
      # Get instance stop time using RegEx
      pattern1 = re.compile(r'\d\d\d\d[-]\d\d[-]\d\d[\s]\d\d[:]\d\d[:]\d\d[\s]...')
      StopTime = pattern1.finditer(instance.state_transition_reason)
  
      for match in StopTime:
        if ageFinder(match.group()) > ec2delta:
          if instance.tags is None:
            continue
          for tag in instance.tags:
            if tag['Key'] == 'Name':

              # Find out if the instance is protected (returns T or F)
              a = str(client.describe_instance_attribute(InstanceId = instance.id, Attribute = 'disableApiTermination'))
              b = a[36]

              print ("Instance Name: " + tag['Value'])
              print ("Instance ID: " + instance.id)
              print ("Region: " + region)
              print ("Instance Type: " + instance.instance_type)
              print ("Launch Time: " + str(instance.launch_time))
              print ("Shutdown Time: " + match.group())
              print ("Termination Protection: " + b)
              print ("")

              # Put instance in appropriate list, depending on it's termination protection state
              if b == "T":
                protEC2.append(instance.id)
              else:
                oldEC2.append(instance.id)

  # Gather a list of the AMI's of instances that are currently running.
  # These will be EXCLUDED from the list of AMI's that will be flagged for deletion
  for instance in instances:
    if instance.state['Name'] == "running":
      runInst.append(instance.image_id)
      


print ("-------------------------------------------------------------------------------")
print ("-------------------------- AMI's older than",amidelta ,"days ---------------------------")
print ("-------------------------------------------------------------------------------")

# Gather a list of AMI's and their respective Snapshots older than the "amidelta" variable

for region in regions:
  client = boto3.client('ec2', region_name=region)
  images = client.describe_images(Owners=['self'])
  
  for ami in images['Images']:
    if ami['VirtualizationType'] == 'hvm':
      if ageFinder(ami['CreationDate']) > amidelta:
        if str(ami['ImageId']) in runInst:
          blockdata = (ami['BlockDeviceMappings'])
          pattern = re.compile(r'snap-[^\']*')
          snap = pattern.finditer(str(blockdata))
          for match in snap:
            activeSnap.append(match.group())

        if str(ami['ImageId']) not in runInst:
          blockdata = (ami['BlockDeviceMappings'])
          pattern = re.compile(r'snap-[^\']*')
          snap = pattern.finditer(str(blockdata))
          for match in snap:
            if ami['ImageId'] not in oldAMI:
              oldAMI.append(ami['ImageId'])
            if match.group() not in oldAMIsnap:
              oldAMIsnap.append(match.group())
            print ("Name: " + ami['Name'])
            print ("Region: " + region)
            print ("AMI ID: " + ami['ImageId'])
            print ("Snap ID: " + match.group())
            print ("Created: " + ami['CreationDate'])
            print ()

    elif ami['VirtualizationType'] != 'hvm':
      blockdata = (ami['BlockDeviceMappings'])
      pattern = re.compile(r'snap-[^\']*')
      snap = pattern.finditer(str(blockdata))
      for match in snap:
        nonhvmsnap.append(match.group())
  
  # Gather a list of the snapshots of running AMI's.
  # These will be EXCLUDED from snapshot deletion

print ("-------------------------------------------------------------------------------")
print ("-------------------- Orphan Snapshots older than",snapdelta ,"days ----------------------")
print ("-------------------------------------------------------------------------------")

# Gather a list of orphaned snapshots older than the "snapdelta" variable
for region in regions:
  client = boto3.client('ec2', region_name=region)
  snaps = client.describe_snapshots(OwnerIds=['self'])

  for snap in snaps['Snapshots']:
    if ageFinder(snap['StartTime']) > snapdelta:
      if snap['SnapshotId'] not in oldAMIsnap:
        if snap['SnapshotId'] not in activeSnap:
          if snap['SnapshotId'] not in oldSnap:
            if snap['SnapshotId'] not in nonhvmsnap:
              oldSnap.append(snap['SnapshotId'])
              print ("Snapshot ID: " + snap['SnapshotId'])
              print ("Creation Date: " + str(snap['StartTime']))
              print ("Region: " + region)
              print ("Size: " + str(snap['VolumeSize']) + " GiB")
              print ()

  # Gather up the total amount of storage the flagged snapshots take up
  for snap in snaps['Snapshots']:
    if str(snap['SnapshotId']) in oldSnap:
      gb.append(snap['VolumeSize'])
    elif str(snap['SnapshotId']) in oldAMIsnap:
      gb.append(snap['VolumeSize'])
  
print ("-------------------------------------------------------------------------------")

# Calculate monthly cost of EBS snapshots
gibsum = sum(gb)
gbsum = gibsum * 1.07374
gbsum = round(gbsum, 1)
gbcost = gbsum * 0.05
snapcost = round(gbcost, 2)

# Gather up the totals and print
number_of_ec2s = len(oldEC2)
number_of_amis = len(oldAMI)
number_of_proec2s = len(protEC2)
number_of_snaps = len(oldSnap) + len(oldAMIsnap)

print ("Number of old EC2's:", number_of_ec2s)
print ()
print ("Old EC2's with Termiantion Protection:", number_of_proec2s)
print (*protEC2, sep = "\n")
print ()

print ("Number of old AMI's:", number_of_amis)
print ("Number of old Snapshots:", number_of_snaps)
print ()
print ("The script found", gbsum, "GiB of EBS Snapshots")
print ("At the AWS standard rate of $0.05/GB per month, we're paying roughly $" + str(snapcost) + " per month")
print ()

# Redirect stdout back to the console and re-print final stats
sys.stdout = original_stdout
print ("-------------------------------------------------------------------------------")
print ("Results are in: ")
print ()
print ("Number of old EC2's:", number_of_ec2s)
print ("Old EC2's with Termiantion Protection:", number_of_proec2s)
print ()

print ("Number of old AMI's:", number_of_amis)
print ("Number of old Snapshots:", number_of_snaps)
print ()
print ("The script found", gbsum, "GB of EBS Snapshots")
print ("At the AWS standard rate of $0.05/GB per month, we're paying roughly $" + str(snapcost) + " per month")
print ()
print ("Please check " + filename + " for a comprehensive list of all resources that were found.")
print ()
print ("Thank you and have a great day!")
print ("------------------------------------------------------------------------------")