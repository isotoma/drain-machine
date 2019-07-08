#!/bin/bash
eval $(minikube docker-env)
docker build -t drain-machine ..
docker build -t drain-machine-test-server .


