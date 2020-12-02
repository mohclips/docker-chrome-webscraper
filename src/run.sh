#!/bin/bash

PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

cd /app

rm -rf /data/*.log /data/chrome-data /data/err_source.html

rm -rf /app/{.cache,.config,.local,.pki}
#sleep 2

#echo "DISPLAY=$DISPLAY"

/usr/bin/xvfb-run -s '-screen 0 1920x1080x24' python -u ./get_portfolio.py 2>&1 > /data/chrome.log
ERR=$?
# not needed in docker container
#./cleanup.sh 2>&1 >> /data/chrome.log

#env>>/opt/iii/chrome.log

if [[ $ERR -ne 0 ]]; then
    echo "ERROR $ERR"
    echo "============================================================================================"
    tail /data/chrome.log
    echo "============================================================================================"
    tail /data/chromedriver.log
    echo "============================================================================================"
    tail -n 20 /data/chrome-data/chrome_debug.log
    echo "============================================================================================"
else
    /usr/bin/awk '/##TOTAL##/{print $2}' /data/chrome.log | tee -a /data/results.log

    #
    # get FTSE values
    #
    ./get_ftse.sh

    #
    # write to mysql
    #
    ./send_to_mysql.py

fi

