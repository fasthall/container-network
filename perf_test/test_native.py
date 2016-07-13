import os
import sys
import csv
import time
from qperftools import *
sys.path.insert(1, os.path.join(sys.path[0], '..'))
from throttle import *

# test native latency
# a process under heavy egress traffic then use tc to throttle 
def test1(filename):
	of = open(filename, 'w')
	w = csv.writer(of)
	cnt = 5
	result = []
	result.append(['bw', 'tcp latency', 'udp latency'])
	for i in range(1, 129):
		drate = str(i * 8 * 1024 * 1024) 
		os.system('sudo tc class change dev eth0 parent 10: classid 10:1 htb rate ' + drate + 'bit')
		tcp_lat = str(nat_tcp('ruby', cnt))
		udp_lat = str(nat_udp('ruby', cnt))
		print(str(i) + 'M, ' + tcp_lat + ', ' + udp_lat)
		result.append([str(i) + 'M', tcp_lat, udp_lat])
		time.sleep(3)
	w.writerows(result)
	of.close()

if __name__ == '__main__':
	test1("proc_lat.csv")
