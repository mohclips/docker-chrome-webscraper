#!/bin/bash

#lazy get of FTSE 

# google now asks for cookies
#w3m -dump "https://www.google.com/search?q=ftse100" | grep -B1 "UKX(INDEXFTSE)" | head -n 1 | awk '{gsub(/,/,""); print $1}' | tee /data/ftse100.log
#w3m -dump "https://www.google.com/search?q=ftse250" | grep -B1 "MCX(INDEXFTSE)" | head -n 1 | awk '{gsub(/,/,""); print $1}' | tee /data/ftse250.log

w3m -dump "https://www.londonstockexchange.com/indices/ftse-100" | grep -A1 "Index value" | tail -n 1 | awk '{gsub(/,/,""); print $1}' | tee /data/ftse100.log

w3m -dump "https://www.londonstockexchange.com/indices/ftse-250" | grep -A1 "Index value" | tail -n 1 | awk '{gsub(/,/,""); print $1}' | tee /data/ftse250.log