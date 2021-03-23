# AWSomeCleaner
This is a chaotic little Python script making use of Boto3 to quickly and efficiently drop cluster bombs on old AWS resources which are sitting around, costing money.

## Usage
1. This script utilizes the AWS credentials stored locally in your environment variables. Configure that using the AWS CLI.
2. Run AWSomeFinder.py to generate a list of old resources.
3. Run AWSomeCleaner.py to clean-up said resources.

The finder will output a list of resources to a text file in the same folder the user is in when they run it. The cleaner will do the same for auditing purposes.

Note: This is a Python3 script. You will need to have the latest release installed in order to run it.

## Details
The script functions by looking up all AWS resources in the account and region specified. It then runs those resources through this criteria:

For EC2 instances:

- The instance is tagged
- The instance is in a STOPPED state
- The instance has remained in a STOPPED state for longer than specified by the user
- The instance does not have termination protection (though this can be ignored if the user wishes)

For AMI's:

- The AMI belongs to the user running the script
- The AMI is older than the number of days specified by the user
- It is an HVM (Hardware Virtual Machine) image
- There are no running EC2 instances which were launched with the AMI

For EBS Snapshots:

- The snapshot belongs to the user running the script
- The snapshot is older than the number of days specified by the user
- The snapshot is NOT attached to an AMI which has running EC2 instances using it

Resources which meet all of those requirements will be flagged, then subsequently deleted.

## All actions taken by this script are IMMEDIATE and PERMANENT. Please exercise extreme caution when using them.