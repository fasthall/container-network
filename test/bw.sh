#!/bin/bash
echo "Running bandwidth test $1"
echo "bandwidth test $1" > bw$1
docker exec ub1 iperf -c ruby.cs.ucsb.edu -r -f k -t $2 -p 5011 > /dev/null &
docker exec ub2 iperf -c csharp.cs.ucsb.edu -r -f k -t $2 -p 5012 > /dev/null &
docker exec ub3 iperf -c clojure.cs.ucsb.edu -r -f k -t $2 -p 5013 >> bw$1

