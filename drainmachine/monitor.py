"""
Periodically fetch all autoscaling groups that have the following tag:

  kubernetes.io/cluster/CLUSTER_NAME

Check if any of the instances in those ASGs have a LifecycleState of Terminating:Wait

If they do, update the configmap `drain-machine-status` with this list of instances.

The daemons running on the nodes will see this and perform the drain action.

"""

import json
import logging
import os
import subprocess
import sys
from time import sleep

import boto3
import requests

from .utils import get_region, instance_id

logger = logging.getLogger("drainmachine")

boto_endpoint = os.getenv("AUTOSCALING_ENDPOINT", None)

def generate_configmap(instances):
    """ Create the drain-machine-status configmap """
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

def get_tags(data):
    """ Convert the AWS ASG tags into something more useful """
    return dict((x['Key'], x['Value']) for x in data)

def get_cluster_groups(cluster, region):
    """ Return a generator of autoscaling groups that have this cluster tag """
    client = boto3.client('autoscaling', region_name=region, endpoint_url=boto_endpoint)
    response = client.describe_auto_scaling_groups()
    for group in response['AutoScalingGroups']:
        tags = get_tags(group['Tags'])
        if 'kubernetes.io/cluster/%s' % cluster in tags:
            yield group

def get_cluster_instances(cluster, region=None):
    """ Return a generator of instances in the terminating state for this cluster """
    if region is None:
        region = get_region()
    for group in get_cluster_groups(cluster, region):
        for instance in group['Instances']:
            if instance['LifecycleState'] == 'Terminating:Wait':
                yield instance['InstanceId']

def run(cluster):
    """ Be a daemon """
    logging.basicConfig(stream=sys.stderr, format='%(asctime)s %(levelname)s %(message)s', level=os.environ.get("LOGLEVEL", "INFO"))
    logging.getLogger('boto3').setLevel(logging.WARNING)
    logging.getLogger('botocore').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logger = logging.getLogger("drainmachine")
    logger.warning("Starting drainmachine updater for cluster '%s'" % cluster)
    old_instances = None
    namespace = os.environ['NAMESPACE']
    while True:
        instances = list(get_cluster_instances(cluster))
        # Only update the configmap if it does not exist, or has changed
        if old_instances is None or old_instances != instances:
            logger.warning("Flagging %d instances for draining" % len(instances))
            configmap = generate_configmap(instances)
            subprocess.run(
                ['/app/kubectl', '-n', namespace, 'apply', '-f', '-'],
                encoding='utf-8',
                input=json.dumps(configmap),
            )
            old_instances = instances
        else:
            logger.debug("No change in draining list")
        sleep(10)
