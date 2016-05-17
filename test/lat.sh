#!/bin/bash
echo "Running latency test $1"
echo "latency test $1" > lat$1
docker exec ub1 iperf -c scheme.cs.ucsb.edu -r -f k -p 5001 -t 4 > /dev/null &
docker exec ub2 iperf -c erlang.cs.ucsb.edu -r -f k -p 5002 -t 4 > /dev/null &

sleep 2
echo "latency under egress"
echo "latency under egress" >> lat$1
docker exec ub3 qperf x10 tcp_lat udp_lat >> lat$1

sleep 4
echo "latency under ingress"
echo "latency under ingress" >> lat$1
docker exec ub3 qperf x10 tcp_lat udp_lat >> lat$1

sleep 2
