import json
import logging
import os
import subprocess
import sys
from time import sleep

from .utils import complete_lifecycle_action, instance_id, spot_terminating

logger = logging.getLogger("drainmachine")

def terminating():
    proc = subprocess.run(
        ['/app/kubectl', 'get', 'configmap', '-n', 'kube-system', 'drain-machine-status', '-ojson'],
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
