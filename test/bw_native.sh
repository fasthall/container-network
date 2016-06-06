#!/bin/bash
echo "Running native bandwidth test $1"
echo "native bandwidth test $1" > bw_native_$1
iperf -c ruby.cs.ucsb.edu -r -t $2 -p 5011 > /dev/null &
iperf -c csharp.cs.ucsb.edu -r -t $2 -p 5012 > /dev/null &
iperf -c clojure.cs.ucsb.edu -r -t $2 -p 5013 > /dev/null &
#iperf -c clojure.cs.ucsb.edu -r -t $2 -p 5013 >> bw_native_$1


