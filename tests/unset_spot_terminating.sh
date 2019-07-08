#!/bin/bash
URL=`minikube service drain-machine-test --url`
curl $URL/unset_spot_terminating