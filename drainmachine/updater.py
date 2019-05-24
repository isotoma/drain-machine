import logging
import sys
from time import sleep

from .utils import get_cluster_instances

logger = logging.getLogger("drainmachine")

def run(cluster):
    logging.basicConfig(stream=sys.stderr)
    print("Starting drainmachine updater for cluster '%s'" % cluster)
    while True:
        instances = list(get_cluster_instances(cluster))
        print(instances)
        sleep(10)
