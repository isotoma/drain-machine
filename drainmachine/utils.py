import logging

import boto3
import requests

logger = logging.getLogger("drainmachine")


def generate_configmap(instances):
    return {
        'apiVersion': 'v1',
        'kind': 'ConfigMap',
        'metadata': {
            'name': 'drain-machine-status',
        },
        'data': {
            'terminating': " ".join(instances),
        },
    }

def get_region():
    response = requests.get("http://169.254.169.254/2016-09-02/dynamic/instance-identity/document")
    return response.json()['region']

def instance_id():
    response = requests.get("http://169.254.169.254/2016-09-02/meta-data/instance-id")
    return response.text

def spot_terminating():
    response = requests.get("http://169.254.169.254/latest/meta-data/spot/instance-action")
    return response.status_code == 200

def get_tags(data):
    return dict((x['Key'], x['Value']) for x in data)

def complete_lifecycle_action():
    region = get_region()
    instance = instance_id()
    client = boto3.client('autoscaling', region_name=region)
    resp = client.describe_auto_scaling_instances(InstanceIds=[instance])
    asg = resp['AutoScalingInstances'][0]['AutoScalingGroupName']
    resp = client.describe_lifecycle_hooks(AutoScalingGroupName=asg)
    hook_names = [
        x['LifecycleHookName'] 
        for x in resp['LifecycleHooks'] 
        if x['LifecycleTransition'] == 'autoscaling:EC2_INSTANCE_TERMINATING'
    ]
    if len(hook_names) == 1:
        resp = client.complete_lifecycle_action(
            LifecycleHookName=hook_names[0],
            AutoScalingGroupName=asg,
            InstanceId=instance,
            LifecycleActionResult='CONTINUE',
        )
        logger.warning("Completed lifecycle action for %s" % instance)

def get_cluster_groups(cluster, region):
    client = boto3.client('autoscaling', region_name=region)
    response = client.describe_auto_scaling_groups()
    for group in response['AutoScalingGroups']:
        tags = get_tags(group['Tags'])
        if 'kubernetes.io/cluster/%s' % cluster in tags:
            yield group

def get_cluster_instances(cluster, region=None):
    if region is None:
        region = get_region()
    for group in get_cluster_groups(cluster, region):
        for instance in group['Instances']:
            if instance['LifecycleState'] == 'Terminating:Wait':
                yield instance['InstanceId']
