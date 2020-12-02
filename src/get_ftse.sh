#!/bin/bash

#lazy get of FTSE 

w3m -dump "https://www.google.com/search?q=ftse100" | grep -B1 "UKX(INDEXFTSE)" | head -n 1 | awk '{gsub(/,/,""); print $1}' > /data/ftse100.log

w3m -dump "https://www.google.com/search?q=ftse250" | grep -B1 "MCX(INDEXFTSE)" | head -n 1 | awk '{gsub(/,/,""); print $1}' > /data/ftse250.log
