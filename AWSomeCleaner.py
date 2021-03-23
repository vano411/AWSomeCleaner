# Please ensure you THOROUGHLY read the README.md file before running this script.

from datetime import datetime
import time
import boto3
import re
import sys

################################################
# \/ \/ \/ CRITICAL CONTROL VARIABLES \/ \/ \/ #
################################################

# This is where the user decides which region the script will run in
print ("------------------------------------------------------------------------------")
print ("Welcome to AWSome Cleaner!")
print ()
print ("Follow these instructions very carefully!")
print ("------------------------------------------------------------------------------")

region = []
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
print ()

while True:
  val2 = input("Enter the number corresponding to your region: ")
  if val2 == "1":
    region = 'us-west-1'
    break
  elif val2 == "2":
    region = 'us-west-2'
    break
  elif val2 == "3":
    region = 'us-east-1'
    break
  elif val2 == "4":
    region = 'us-east-2'
    break
  elif val2 == "5":
    region = 'ap-northeast-1'
    break
  elif val2 == "6":
    region = 'eu-west-1'
    break
  elif val2 == "7":
    region = 'eu-west-2'
    break
  elif val2 == "8":
    region = 'ap-southeast-1'
    break
  elif val2 == "9":
    region = 'ap-southeast-2'
    break
  elif val2 == "10":
    region = 'sa-east-1'
    break

# This is where the user decides the maximum age of things that will be kept
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

print ("------------------------------------------------------------------------------")

# This is where the user decides if Termination Protection on EC2 instances will be taken into account
print ("Should EC2 Termination Protection be ignored?")
print ("1. No - DO NOT touch instances which are protected!")
print ("2. Yes - Flag protected instances all the same!")
print ()

while True:
  val = input("Select 1 or 2: ")
  if val == "1":
    ignoreProtection = False
    break
  elif val == "2":
    ignoreProtection = True
    break

################################################
# /\ /\ /\ CRITICAL CONTROL VARIABLES /\ /\ /\ #
################################################

print ("------------------------------------------------------------------------------")
print ("Thank you! Please stand by while carpet bombing commences...")
print ("------------------------------------------------------------------------------")
print ("EC2 clean-up is in progress...")
print ()

# Create text file and redirect stdout to that file
timestr = time.strftime("%Y%m%d-%H%M%S")
dt = time.strftime("%m/%d/%Y %H:%M:%S %Z")
filename = "AWSomeCleaner-"+str(timestr)+"-"+region+".txt"
original_stdout = sys.stdout
sys.stdout = open(filename, 'a+')

# Print AWS user, account and region info at head of file for auditing reasons
iam = boto3.resource('iam', region_name=region)
account_id = iam.CurrentUser().arn.split(':')[4]
user = iam.CurrentUser().arn.split(':')[5]
print ("AWSome Cleaner has been invoked!")
print ()
print ("AWS Account ID:", account_id)
print ("IAM User:", user)
print ("Date/Time:", dt)
print ("Region:", region)
print ()

ec2 = boto3.resource('ec2', region_name=region)
client = boto3.client('ec2', region_name=region)
instances = ec2.instances.filter()

# Creating lists which will be populated
oldEC2 = []
protEC2 = []
oldAMI = []
oldAMIsnap = []
oldSnap = []
runInst = []
activeSnap = []
nonhvmsnap = []

# Function which takes the creation date of an AWS resource and returns its age in days
def ageFinder(day):
    cdate1 = str(day)
    cdate2 = cdate1[0:10]
    date1 = datetime.strptime(cdate2, "%Y-%m-%d")
    date2 = datetime.now()
    diff = date2 - date1
    return diff.days

##############################################################################
# THIS PART OF THE SCRIPT DETONATES OLD EC2 INSTANCES THAT HAVE BEEN STOPPED #
##############################################################################

print ("-------------------------------------------------------------------------------")
print ("-------------------------- EC2's older than",ec2delta ,"days ---------------------------")
print ("-------------------------------------------------------------------------------")
print ()

# Gather a list of STOPPED instances older than the "ec2delta" variable
for instance in instances:
  if instance.state['Name'] == "stopped":
    pattern1 = re.compile(r'\d\d\d\d[-]\d\d[-]\d\d[\s]\d\d[:]\d\d[:]\d\d[\s]...')
    StopTime = pattern1.finditer(instance.state_transition_reason)
  
    for match in StopTime:
      if ageFinder(match.group()) > ec2delta:
        if instance.tags is None:
          continue
        for tag in instance.tags:
          if tag['Key'] == 'Name':
            a = str(client.describe_instance_attribute(InstanceId = instance.id, Attribute = 'disableApiTermination'))
            b = a[36]

            # Append the resource details to the text file
            print ("Instance Name: " + tag['Value'])
            print ("Instance ID: " + instance.id)
            print ("Region: " + region)
            print ("Instance Type: " + instance.instance_type)
            print ("Launch Time: " + str(instance.launch_time))
            print ("Shutdown Time: " + match.group())
            print ("Termination Protection: " + b)
            print ("")

            # Determine which list to put the EC2 instance in based on Termination Protection flag
            if b == "T":
              protEC2.append(instance.id)
            elif b == "F":
              oldEC2.append(instance.id)
print ()
print ("-------------------------------------------------------------------------------")
print ()
print ("The following instances have been TERMINATED!!!")
print (*oldEC2, sep="\n")
print ()

# Terminate EC2 instances which are NOT protected
for id in oldEC2:
  ec2.Instance(id).terminate()

# What to do with EC2 instances which have termiation protection?
# If ignoreProtection variable is set to TRUE, the instances will be stripped of protection status and terminated
if ignoreProtection == True and len(protEC2) > 0:
  print ("Ignore Protection is set to TRUE")
  print ("The following instances will be stripped of protection and TERMIANTED!!!")
  print (*protEC2, sep="\n")
  print ()
  for id in protEC2:
    ec2.Instance(id).modify_attribute(
      DisableApiTermination={
        'Value': False
      }
    )
    ec2.Instance(id).terminate()

# If ignoreProtection is set to FALSE, instances will not be touched
elif ignoreProtection == False and len(protEC2) > 0:
  print ("Ignore Protection is set to FALSE")
  print ("The following instances are protected and WILL NOT be touched")
  print (*protEC2, sep="\n")
  print ()

elif len(protEC2) == 0:
  print ("No protected EC2 instances were found.")
  print ()

# Let the user know things are happening so they don't assume it froze
sys.stdout = original_stdout

print ("EC2 clean-up is complete!")
print ()
print ("AMI clean-up is now in progress...")
print ()

sys.stdout = open(filename, 'a+')

##################################################################################
# THIS PART OF THE SCRIPT DETONATES OLD AMI'S AND THEIR RESPECTIVE EBS SNAPSHOTS #
##################################################################################

print ("-------------------------------------------------------------------------------")
print ("-------------------------- AMI's older than",amidelta ,"days ---------------------------")
print ("-------------------------------------------------------------------------------")
print ()

# Gather a list of the AMI's which currently running instances were launched with
# These will be EXCLUDED from the list of AMI's that will be flagged for deletion
for instance in ec2.instances.all():
  if instance.state['Name'] == "running":
    runInst.append(instance.image_id)

images = client.describe_images(Owners=['self'])

for ami in images['Images']:
  if ami['VirtualizationType'] == 'hvm':
    if ageFinder(ami['CreationDate']) > amidelta:

      # Gather a list of the snapshots of the AMI's that have running instances
      # These will be EXCLUDED from the list of snapshots will be flagged for deletion
      if str(ami['ImageId']) in runInst:
        blockdata = (ami['BlockDeviceMappings'])
        pattern = re.compile(r'snap-[^\']*')
        snap = pattern.finditer(str(blockdata))
        for match in snap:
          activeSnap.append(match.group())

      # Gather a list of AMI's and their respective Snapshots older than the "amidelta" variable
      if ami['ImageId'] not in runInst:
        blockdata = (ami['BlockDeviceMappings'])
        pattern = re.compile(r'snap-[^\']*')
        snap = pattern.finditer(str(blockdata))
        for match in snap:
          
          # Append the resource details to the text file
          print ("Name: " + ami['Name'])
          print ("Region: " + region)
          print ("AMI ID: " + ami['ImageId'])
          print ("Snap ID: " + match.group())
          print ("Created: " + ami['CreationDate'])
          print ()
          
          # Dedup, then add resources to lists
          if ami['ImageId'] not in oldAMI:
            oldAMI.append(ami['ImageId'])
          if match.group() not in oldAMIsnap:
            oldAMIsnap.append(match.group())
  
  # Gather a list of the snapshots of non-HVM AMI's
  # These will be EXCLUDED from the list of snapshots will be flagged for deletion
  elif ami['VirtualizationType'] != 'hvm':
    blockdata = (ami['BlockDeviceMappings'])
    pattern = re.compile(r'snap-[^\']*')
    snap = pattern.finditer(str(blockdata))
    for match in snap:
      nonhvmsnap.append(match.group())

print ("The following AMI's have been DEREGISTERED!!!")
print (*oldAMI, sep="\n")
print ()

# Deregister the AMI's
for id in oldAMI:
  client.deregister_image(ImageId=id)

print ()
print ("The following snapshots were attached to those AMI's and have been DELETED!!!")
print (*oldAMIsnap, sep="\n")
print ()

# Delete the snapshots of those AMI's
for id in oldAMIsnap:
  client.delete_snapshot(SnapshotId=id)

# Let the user know things are happening so they don't assume it froze
sys.stdout = original_stdout

print ("AMI clean-up is complete!")
print ()
print ("Snapshot clean-up is now in progress...")
print ()

sys.stdout = open(filename, 'a+')

##########################################################
# THIS PART OF THE SCRIPT DELETES OLD ORPHANED SNAPSHOTS #
##########################################################

print ("-------------------------------------------------------------------------------")
print ("-------------------- Orphan Snapshots older than",snapdelta ,"days ----------------------")
print ("-------------------------------------------------------------------------------")
print ()

snaps = client.describe_snapshots(OwnerIds=['self'])

# Gather a list of snapshots older than the "snapdelta" variable
for snap in snaps['Snapshots']:
  if ageFinder(snap['StartTime']) > snapdelta:
    if str(snap['SnapshotId']) not in oldAMIsnap:
      if str(snap['SnapshotId']) not in activeSnap:
        if str(snap['SnapshotId']) not in oldSnap:
          if str(snap['SnapshotId']) not in nonhvmsnap:

            # Dedup, then add resources to lists
            oldSnap.append(snap['SnapshotId'])
            
            # Append the resource details to the text file
            print ("Snapshot ID: " + snap['SnapshotId'])
            print ("Creation Date: " + str(snap['StartTime']))
            print ("Region: " + region)
            print ("Size: " + str(snap['VolumeSize']) + " GiB")
            print ()

print ("The following snapshots have been DELETED!!!")
print (*oldSnap, sep="\n")
print ()

# Delete the snapshots
for id in oldSnap:
  client.delete_snapshot(SnapshotId=id)

# Let the user know things are happening so they don't assume it froze
sys.stdout = original_stdout

print ("Snapshot clean-up is complete!")
print ()

sys.stdout = open(filename, 'a+')

##################################################
# THIS PART OF THE SCRIPT GENERATES A BODY COUNT #
##################################################

print ("------------------------------------------------------------------------------")
print ("Damage report!")
print ()

number_of_amis = len(oldAMI)
number_of_snaps = len(oldSnap) + len(oldAMIsnap)

if ignoreProtection == True and len(protEC2) > 0:
  number_of_ec2s = len(oldEC2) + len (protEC2)
  print ("Number of old EC2's terminated:", number_of_ec2s)

elif ignoreProtection == False and len(protEC2) > 0:
  number_of_ec2s = len(oldEC2)
  print ("Number of old EC2's terminated:", number_of_ec2s)
  print ()
  print ("These instances have Termination Protection and were NOT touched, as instructed:")
  print (*protEC2, sep="\n")
  print ()

else:
  number_of_ec2s = len(oldEC2)
  print ("Number of old EC2's terminated:", number_of_ec2s)

print ("Number of old AMI's deregistered:", number_of_amis)
print ("Number of old Snapshots deleted:", number_of_snaps)

sys.stdout = original_stdout

print ("------------------------------------------------------------------------------")
print ("ALL DONE!")
print ()
print ("AWSome Cleaner ran successfully. Check out " + filename + " for detailed information on the resources that were modified.")
print ()
print ("Thank you and have a great day!")
print ("------------------------------------------------------------------------------")