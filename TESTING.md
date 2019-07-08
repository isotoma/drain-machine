# Testing drain-machine

There is a basic test harness designed to be run in minikube.

To set this up:

    minikube start
    ./build_test.sh
    cd testing
    kubectl apply -f manifest.yaml

At this point there is a daemon and monitor running, and a test server that mocks
various bits of AWS.

You can then do:

    ./set_terminating.sh minikube

To fake the minikube instance being terminated by an ASG.

Or:

    ./set_spot_terminating.sh

To fake a spot instance termination message.

Note that because minikube has only a single node, which is also the master, once drain-machine has cordoned and drained the node it is irrecoverable!

This makes the testing useful for smoke testing, but for a proper end-to-end test you need a real cluster.
