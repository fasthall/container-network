#!/bin/bash
echo "Running bandwidth test $1"
echo "bandwidth test $1" > bw$1
docker exec ub1 iperf -c scheme.cs.ucsb.edu -r -f k -t $2 -p 5001 > /dev/null &
docker exec ub2 iperf -c erlang.cs.ucsb.edu -r -f k -t $2 -p 5002 > /dev/null &
docker exec ub3 iperf -c x10.cs.ucsb.edu -r -f k -t $2 -p 5003 >> bw$1

