#!/bin/bash

cd build/init
docker build -t dwh-init . -f DockerFile

cd ../llm
docker build -t dwh-llm . -f DockerFile
