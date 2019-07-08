#!/bin/bash
URL=`minikube service drain-machine-test --url`
curl $URL/set_spot_terminating