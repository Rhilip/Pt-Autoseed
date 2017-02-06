#!/bin/bash
cd `dirname $0`
eval $(ps -ef | grep "[0-9] python3 autoseed\\.py m" | awk '{print "kill "$2}')
nohup python3 autoseed.py m>> /dev/null 2>&1 &