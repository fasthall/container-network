docker exec ub1 qperf ruby.cs.ucsb.edu -t 5 tcp_bw &
docker exec ub2 qperf csharp.cs.ucsb.edu -t 5 tcp_bw &
docker exec ub3 qperf clojure.cs.ucsb.edu -t 5 tcp_bw &
