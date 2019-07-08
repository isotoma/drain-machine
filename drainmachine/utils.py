
import os

import requests

# Testing entrypoints
region_endpoint = os.getenv('REGION_ENDPOINT', "http://169.254.169.254/2016-09-02/dynamic/instance-identity/document")
instance_id_endpoint = os.getenv('INSTANCE_ID_ENDPOINT', "http://169.254.169.254/2016-09-02/meta-data/instance-id")

def get_region():
    response = requests.get(region_endpoint)
    return response.json()['region']

def instance_id():
    response = requests.get(instance_id_endpoint)
    return response.text
