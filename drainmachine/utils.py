import boto3
import requests


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

def get_tags(data):
    return dict((x['Key'], x['Value']) for x in data)

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
