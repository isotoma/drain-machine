#!/bin/bash
URL=`minikube service drain-machine-test --url`
curl $URL/set_terminating_asg?instances=$1