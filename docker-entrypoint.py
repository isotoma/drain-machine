#! /usr/bin/env python

import click

from drainmachine import drainer, updater


@click.group()
def drainmachine():
    pass

@drainmachine.command()
@click.option('--cluster', help="Cluster name to find in tag")
def update(cluster):
    if cluster is None:
        raise ValueError("Cluster must be specified")
    updater.run(cluster)
    
@drainmachine.command()
def daemon():
    drainer.run()

drainmachine()
