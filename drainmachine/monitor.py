import json
import logging
import subprocess
import sys
from time import sleep

from .utils import generate_configmap, get_cluster_instances


def run(cluster):
    logging.basicConfig(stream=sys.stderr, format='%(asctime)s %(levelname)s %(message)s')
    logger = logging.getLogger("drainmachine")
    logger.warning("Starting drainmachine updater for cluster '%s'" % cluster)
    old_instances = None
    while True:
        instances = list(get_cluster_instances(cluster))
        if old_instances is None or old_instances != instances:
            logger.warning("Flagging %d instances for draining" % len(instances))
            configmap = generate_configmap(instances)
            subprocess.run(
                ['/app/kubectl', '-n', 'kube-system', 'apply', '-f', '-'],
                encoding='utf-8',
                input=json.dumps(configmap),
            )
            old_instances = instances
        else:
            logger.debug("No change in draining list")
        sleep(10)
