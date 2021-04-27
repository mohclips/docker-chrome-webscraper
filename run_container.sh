#!/bin/bash

cd /home/nick/workspaces/docker-iii/

docker-compose up 2>&1 | tee last_run.log

