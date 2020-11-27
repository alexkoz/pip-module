import os
import sys
import boto3
import datetime
import time

current_date = datetime.datetime.strptime(str(datetime.datetime.now()), '%Y-%m-%d %H:%M:%S.%f')

application_branch = os.environ['APP_BRANCH']
as_client = boto3.client('autoscaling',
                         aws_access_key_id=os.environ['DEPLOY_ACCESS'],
                         aws_secret_access_key=os.environ['DEPLOY_SECRET'],
                         region_name=os.environ['DEPLOY_REGION'])

ec2_client = boto3.client('ec2',
                          aws_access_key_id=os.environ['DEPLOY_ACCESS'],
                          aws_secret_access_key=os.environ['DEPLOY_SECRET'],
                          region_name=os.environ['DEPLOY_REGION'])


def wait_till_image_ready(client, image_id: str):
    images_description_response = client.describe_images(ImageIds=[image_id])
    print(f'Image status:{images_description_response["Images"][0]["State"]}')
    while images_description_response['Images'][0]['State'] != 'available':
        time.sleep(10)
        print(f'Image status:{images_description_response["Images"][0]["State"]}')
        images_description_response = client.describe_images(ImageIds=[image_id])


response_autscaling_groups = as_client.describe_auto_scaling_groups()
copy_autoscaling_group = None
for as_group in response_autscaling_groups['AutoScalingGroups']:
    if application_branch in str(as_group['AutoScalingGroupName']).lower():
        copy_autoscaling_group = as_group
    elif application_branch == 'sandy' and 'dev' in str(as_group['AutoScalingGroupName']).lower():
        copy_autoscaling_group = as_group

copy_instance = copy_autoscaling_group['Instances'][0]
instance_name = f'ai-{application_branch}-{current_date}'.replace(' ', '').replace(':', '')

# create_image_reponse = ec2_client.create_image(InstanceId=copy_instance['InstanceId'],
#                                               Name=instance_name,
#                                               Description=instance_name)

image_id = 'ami-0341d08f183087b2f'  # create_image_reponse['ImageId']
wait_till_image_ready(ec2_client, image_id)

copy_launch_configurations = as_client.describe_launch_configurations(
    LaunchConfigurationNames=[copy_autoscaling_group['LaunchConfigurationName']])
copy_lc = copy_launch_configurations['LaunchConfigurations'][0]
create_launch_config_reponse = as_client.create_launch_configuration(
    LaunchConfigurationName=instance_name,
    ImageId=image_id,
    KeyName=copy_lc['KeyName'],
    SecurityGroups=copy_lc['SecurityGroups'],
    InstanceType=copy_lc['InstanceType'],
    InstanceMonitoring={
        'Enabled': False
    },
    SpotPrice=copy_lc['SpotPrice'],
    EbsOptimized=False,
    AssociatePublicIpAddress=True
)

update_scaling_group_response = as_client.update_auto_scaling_group(
    AutoScalingGroupName=copy_autoscaling_group['AutoScalingGroupName'],
    LaunchConfigurationName=instance_name)

all_instances = ec2_client.describe_instances()

reservations = all_instances['Reservations']
for reservation in reservations:
    if reservation['Instances'][0]['InstanceType'] == 'm5.xlarge' \
            and application_branch in str(reservation['Instances'][0]['Tags'][0]['Value']).lower():
        reservation['Instances'][0]
response_launch_configurations = as_client.describe_launch_configurations()
response_launch_configurations = as_client.describe_autscaling_groups()
response_launch_configurations
sys.exit(0)
