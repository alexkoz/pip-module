import datetime
import os
import sys
import argparse


import boto3

current_date = datetime.datetime.strptime(str(datetime.datetime.now()), '%Y-%m-%d %H:%M:%S.%f')

if __name__ == '__main__':

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--branch', required=True,
                        help='branch.')

    args = parser.parse_args()
    application_branch = args.branch
    print(f"Start discovering instances for branch:{application_branch}")
    session = boto3.session.Session(profile_name='clipnow-deploy', region_name=os.environ['AWS_REGION'])
    as_client = session.client('autoscaling')
    ec2_client = session.client('ec2')

    response_autscaling_groups = as_client.describe_auto_scaling_groups()
    copy_autoscaling_group = None
    for as_group in response_autscaling_groups['AutoScalingGroups']:
        if application_branch in str(as_group['AutoScalingGroupName']).lower():
            copy_autoscaling_group = as_group
        elif application_branch == 'sandy' and 'dev' in str(as_group['AutoScalingGroupName']).lower():
            copy_autoscaling_group = as_group


    for instance in copy_autoscaling_group['Instances']:

        instance_description = all_instances = ec2_client.describe_instances(InstanceIds=[instance['InstanceId']])
        print(instance_description['Reservations'][0]['Instances'][0]['PublicIpAddress'])

sys.exit(0)

