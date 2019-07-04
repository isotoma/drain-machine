# drain-machine

## Introduction

Drain Machine is a tool that drains kubernetes nodes in response to termination notifications caused by the following AWS EC2 lifecycle events:

- When an instance is being terminated by an Autoscaling Group
- When a spot instance is notified of impending termination because of spot availability changes

## FAQ

### What is draining

Draining is the process of evicting all of the non-daemonset pods, so they will restart on other nodes.

### What actual command is used to drain the nodes

    kubectl drain --delete-local-data --ignore-daemonsets --force --timeout=60s

Note that this is a pretty forceful drain - but then the instance is going to be terminated!

## Installation

Before using drain-machine you have to ensure your Autoscaling Groups are tagged properly, and that they have the appropriate lifecycle hooks (see below).

Then the easiest way to deploy drain-machine is using the incubator chart from the helm repository.

### Configuring your autoscaling groups

Ensure the a tag of this format exists on the ASG:

    Tags:
      - Key: kubernetes.io/cluster/CLUSTER_NAME
        Value: owned
        PropagateAtLaunch: true

Note that this is the same tag expected by the kubernetes cluster autoscaler, so it may well already be present.

You need to pass CLUSTER_NAME to the drain-machine monitor with the --cluster argument, or in the helm chart as drain.cluster.

You should also include:

    LifecycleHookSpecificationList:
      - LifecycleHookName: termination
        LifecycleTransition: autoscaling:EC2_INSTANCE_TERMINATING

In the properties of your autoscaling group. This will cause the ASG to pause in termination, until Drain Machine tells it to continue with termination, once the instance
has been completed drained.

## How it works

The software runs in two modes:

### Monitor mode

This runs as a deployment, looking at all Autoscaling Groups with the tag above and looking for instances that are terminating. It updates a configmap if any of the instances are terminating.

### Daemon mode

In this mode it runs within a Daemonset. The daemon in the daemonset is responsible for actually draining the node.

It checks if this instance is in the configmap as a terminating instance, and also checks the spot instance termination status by looking at the metadata endpoint:

http://169.254.169.254/latest/meta-data/spot/instance-action

Which is only available to the instances themselves.

If either of this conditions are true then it drains the node.
