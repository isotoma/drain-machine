#! /usr/bin/env python

import click

from drainmachine import drainer, monitor


@click.group()
def drainmachine():
    pass

@drainmachine.command()
@click.option('--cluster', help="Cluster name to find in tag")
def update(cluster):
    if cluster is None:
        raise ValueError("Cluster must be specified")
    monitor.run(cluster)
    
@drainmachine.command()
def daemon():
    drainer.run()

drainmachine()
