#!/bin/bash
echo "Running latency case $1"
docker exec ub1 iperf -c scheme.cs.ucsb.edu -f k -t 5 > /dev/null &
docker exec ub2 iperf -c erlang.cs.ucsb.edu -f k -t 5 > /dev/null &
sleep 2
docker exec ub3 qperf x10 tcp_lat udp_lat
sleep 3
