"""
This should be run as part of a daemonset on every instance in your cluster.

Every 10 seconds it:

- checks if this instance is in the list of terminating instances in the configmap
- checks if this instance is being terminated for spot reasons

if either of those things is true then the node is cordoned and drained

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

def spot_terminating():
    """ Check if this spot instance is terminating. If the instance-action endpoint exists, then we're terminating """

    response = requests.get("http://169.254.169.254/latest/meta-data/spot/instance-action")
    return response.status_code == 200


def complete_lifecycle_action():
    """ Find an autoscaling lifecycle hook, if it exists, for the termination of this instance.
    If such a hook exists then mark the hook as completed and tell the autoscaling group to continue.
    """
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


def terminating():
    """ Check if this instance is marked as terminating in the configmap. """
    namespace = os.environ['NAMESPACE']
    proc = subprocess.run(
        ['/app/kubectl', 'get', 'configmap', '-n', namespace, 'drain-machine-status', '-ojson'],
        capture_output=True,
    )
    if proc.returncode == 0:
        try:
            configmap = json.loads(proc.stdout)
        except json.decoder.JSONDecodeError:
            logger.exception("Error in JSON Decoding of ConfigMap")
            return False
        terminating = configmap['data']['terminating'].split()
        instance = instance_id()
        return instance in terminating
    else:
        return False

def evict():
    """ Execute the drain command """
    node_name = os.environ['NODE_NAME']
    while True:
        proc = subprocess.run(
            ['/app/kubectl', 'drain', '--delete-local-data', '--ignore-daemonsets', '--force', '--timeout=60s', node_name]
        )
        if proc.returncode != 0:
            print("Not all pods can be evicted, retrying")
        else:
            return
        sleep(10)

def run():
    """ Do the daemon stuff. """
    logging.basicConfig(stream=sys.stderr, format='%(asctime)s %(levelname)s %(message)s')
    logger.warning("Starting drainmachine daemon")
    while True:
        spot = spot_terminating()
        cycle = terminating()
        if spot or cycle:
            print("Node is terminating, draining")
            evict()
            complete_lifecycle_action()
        sleep(10)
