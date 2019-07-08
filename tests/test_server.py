import json
import sys

from flask import Flask, jsonify, request

app = Flask(__name__)


terminating_instances = []
spot_terminating_flag = False

@app.route("/set_terminating_asg")
def set_terminating_asg():
    global terminating_instances
    terminating_instances = request.args.get("instances").split(",")
    return "", 200

@app.route("/set_spot_terminating")
def set_spot_terminating():
    global spot_terminating_flag
    spot_terminating_flag = True
    return "", 200

@app.route("/unset_spot_terminating")
def unset_spot_terminating():
    global spot_terminating_flag
    spot_terminating_flag = False
    return "", 200

@app.route("/region")
def region():
    return jsonify({"region": "minikube"})

@app.route("/instance_id")
def instance_id():
    return "minikube"

@app.route("/spot_terminating")
def spot_terminating():
    if spot_terminating_flag:
        return "", 200
    else:
        return "", 404

@app.route("/autoscaler", methods=['POST'])
def autoscaler():
    action = request.values.get("Action")
    if action == 'DescribeAutoScalingGroups':
        print("DescribeAutoScalingGroups called, sending", terminating_instances, file=sys.stderr)
        instances = ["""
        <member>
        <LifecycleState>Terminating:Wait</LifecycleState>
        <InstanceId>%s</InstanceId>
        </member>
        """ % i for i in terminating_instances]
        return """
        <DescribeAutoScalingGroupsResponse xmlns="http://autoscaling.amazonaws.com/doc/2011-01-01/">
          <DescribeAutoScalingGroupsResult>
            <AutoScalingGroups>
              <member>
                <Tags>
                  <member>
                    <Key>kubernetes.io/cluster/cluster</Key>
                    <Value>owned</Value>
                  </member>
                </Tags>
                <Instances>%s</Instances>
              </member>
            </AutoScalingGroups>
          </DescribeAutoScalingGroupsResult>
        </DescribeAutoScalingGroupsResponse>
        """ % instances
    elif action == 'DescribeAutoScalingInstances':
        # the request is for a specific named instance, and finds the group in which
        # the instance resides
        return """
        <DescribeAutoScalingInstancesResponse xmlns="http://autoscaling.amazonaws.com/doc/2011-01-01/">
          <DescribeAutoScalingInstancesResult>
            <AutoScalingInstances>
              <member>
                <AutoScalingGroupName>my-asg</AutoScalingGroupName>
              </member>
            </AutoScalingInstances>
          </DescribeAutoScalingInstancesResult>
        </DescribeAutoScalingInstancesResponse> 
        """
    elif action == 'DescribeLifecycleHooks':
        print("DescribeLifeCycleHooks called", file=sys.stderr)
        return """
        <DescribeLifecycleHooksResponse xmlns="http://autoscaling.amazonaws.com/doc/2011-01-01/">
        <DescribeLifecycleHooksResult>
            <LifecycleHooks>
            <member>
                <LifecycleTransition>autoscaling:EC2_INSTANCE_TERMINATING</LifecycleTransition> 
                <LifecycleHookName>hookname</LifecycleHookName> 
            </member>
            </LifecycleHooks>
        </DescribeLifecycleHooksResult>
        </DescribeLifecycleHooksResponse>         
        """ % instances
    elif action == 'CompleteLifecycleAction':
        return "", 200
    else:
        print("Unexpected action", file=sys.stderr)
        print(repr(request.values), file=sys.stderr)
        return "", 500
