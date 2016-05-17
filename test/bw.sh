#!/bin/bash
echo "Running case $1"
docker exec ub1 iperf -c scheme.cs.ucsb.edu -f k -t 60 > case$1_ub1 &
docker exec ub2 iperf -c erlang.cs.ucsb.edu -f k -t 60 > case$1_ub2 &
docker exec ub3 iperf -c x10.cs.ucsb.edu -f k -t 60 > case$1_ub3 &

