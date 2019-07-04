
import requests


def get_region():
    response = requests.get("http://169.254.169.254/2016-09-02/dynamic/instance-identity/document")
    return response.json()['region']

def instance_id():
    response = requests.get("http://169.254.169.254/2016-09-02/meta-data/instance-id")
    return response.text
