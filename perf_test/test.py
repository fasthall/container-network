import os
import sys
import csv
import time
from qperftools import *
sys.path.insert(1, os.path.join(sys.path[0], '..'))
from throttle import *

# test native latency
def test1():
	cnt = 10
	print('Testing native latency')
	print('TCP latency:')
	print('ruby: ' + str(nat_tcp('ruby', cnt)))
	print('csharp: ' + str(nat_tcp('csharp', cnt)))
	print('clojure: ' + str(nat_tcp('clojure', cnt)))
	print('UDP latency:')
	print('ruby: ' + str(nat_udp('ruby', cnt)))
	print('csharp: ' + str(nat_udp('csharp', cnt)))
	print('clojure: ' + str(nat_udp('clojure', cnt)))

# test latency from container
def test2():
	cnt = 10
	print('Testing container latency')
	print('TCP latency:')
	print('ruby: ' + str(tcp('ub1', 'ruby', cnt)))
	print('csharp: ' + str(tcp('ub1', 'csharp', cnt)))
	print('clojure: ' + str(tcp('ub1', 'clojure', cnt)))
	print('UDP latency:')
	print('ruby: ' + str(udp('ub1', 'ruby', cnt)))
	print('csharp: ' + str(udp('ub1', 'csharp', cnt)))
	print('clojure: ' + str(udp('ub1', 'clojure', cnt)))

# test latency under ingress traffic
# prepare ub1 ub2
# ub2 under heavy ingress traffic
def test3(filename):
	of = open(filename, 'w')
	w = csv.writer(of)
	cnt = 5
	result = []
	result.append(['bandwidth', 'tcp latency', 'udp latency'])
	result.append(['unlimited', str(tcp('ub1', 'ruby', cnt)), str(udp('ub1', 'ruby', cnt))])
	for i in range(1, 129):
		drate = str(i) + 'M'
		throttle(('test3 ub2 -d ' + drate).split(' '))
		tcp_lat = str(tcp('ub1', 'ruby', cnt))
		udp_lat = str(udp('ub1', 'ruby', cnt))
		result.append([drate, tcp_lat, udp_lat])
		time.sleep(3)
	w.writerows(result)
	of.close()

# test latency under egress traffic
# prepare ub1 ub2
# ub2 under heavy egress traffic
def test4(filename):
	of = open(filename, 'w')
	w = csv.writer(of)
	cnt = 5
	result = []
	result.append(['bandwidth', 'tcp latency', 'udp latency'])
	result.append(['unlimited', str(tcp('ub1', 'ruby', cnt)), str(udp('ub1', 'ruby', cnt))])
	for i in range(1, 129):
		urate = str(i) + 'M'
		throttle(('test4 ub2 -u ' + urate).split(' '))
		tcp_lat = str(tcp('ub1', 'ruby', cnt))
		udp_lat = str(udp('ub1', 'ruby', cnt))
		result.append([urate, tcp_lat, udp_lat])
		time.sleep(3)
	w.writerows(result)
	of.close()

# test latency under no traffic with different throttle
# prepare ub1
def test5(filename):
	of = open(filename, 'w')
	w = csv.writer(of)
	cnt = 10
	result = []
	result.append(['unlimited', str(udp('ub1', 'ruby', cnt))])
	for i in range(1, 129):
		drate = str(i) + 'M'
		throttle(('test5 ub1 -u ' + drate).split(' '))
		lat = str(tcp('ub1', 'ruby', cnt))
		print(lat)
		result.append([drate, lat])
		time.sleep(1)
	w.writerows(result)
	of.close()

# test latency under no traffic with different throttle
# prepare ub1
def test6(filename):
	of = open(filename, 'w')
	w = csv.writer(of)
	cnt = 10
	result = []
	result.append(['unlimited', str(udp('ub1', 'ruby', cnt))])
	for i in range(1, 129):
		drate = str(i) + 'M'
		throttle(('test6 ub1 -d ' + drate).split(' '))
		lat = str(tcp('ub1', 'ruby', cnt))
		print(lat)
		result.append([drate, lat])
		time.sleep(1)
	w.writerows(result)
	of.close()

# test latency with different containers number
def test7(filename):
	print('WARNING: This will remove all the containers')
	raw_input('Ctrl + C to terminate')
	of = open(filename, 'w')
	w = csv.writer(of)
	cnt = 5
	result = [['Container #', 'TCP latency', 'UDP latency']]
	os.system('docker stop $(docker ps -aq)')
	os.system('docker rm $(docker ps -aq)')
	for i in range(1, 65):
		os.system('docker run -id --name ub' + str(i) + ' fasthall/iperf_qperf bash')
		print(str(i) + ' containers now...')
		tcp_lat = tcp('ub1', 'ruby', cnt)
		udp_lat = udp('ub1', 'ruby', cnt)
		result.append([i, tcp_lat, udp_lat])
		time.sleep(1)
	w.writerows(result)
	of.close()

# ub1 &ub2 under heavy ingress
# prepare ub1 ub2 ub3
def test8(filename):
	of = open(filename, 'w')
	w = csv.writer(of)
	cnt = 5
	result = [['ub1 bw', 'ub2 bw', 'ub3 tcp_lat', 'ub4 udp lat']]
	result.append(['unlimited', 'unlimited', str(tcp('ub3', 'clojure', cnt)), str(udp('ub3', 'clojure', cnt))])
	for i in range(1, 65, 2):
		drate = str(i) + 'M'
		throttle(('test8 ub1 -d ' + drate).split(' '))
		throttle(('test8 ub2 -d ' + drate).split(' '))
		time.sleep(5)
		tcp_lat = str(tcp('ub3', 'clojure', cnt))
		udp_lat = str(udp('ub3', 'clojure', cnt))
		result.append([drate, drate, tcp_lat, udp_lat])
	w.writerows(result)
	of.close()

# ub1 &ub2 under heavy egress
# prepare ub1 ub2 ub3
def test9(filename):
	of = open(filename, 'w')
	w = csv.writer(of)
	cnt = 5
	result = [['ub1 bw', 'ub2 bw', 'ub3 tcp_lat', 'ub4 udp lat']]
	result.append(['unlimited', 'unlimited', str(tcp('ub3', 'clojure', cnt)), str(udp('ub3', 'clojure', cnt))])
	for i in range(1, 65, 2):
		urate = str(i) + 'M'
		throttle(('test9 ub1 -u ' + urate).split(' '))
		throttle(('test9 ub2 -u ' + urate).split(' '))
		time.sleep(2)
		tcp_lat = str(tcp('ub3', 'clojure', cnt))
		udp_lat = str(udp('ub3', 'clojure', cnt))
		result.append([urate, urate, tcp_lat, udp_lat])
	w.writerows(result)
	of.close()

if __name__ == '__main__':
	#test1()
	#test2()
	#test3('test3.csv')
	test4('retest4.csv')
	#test5('ub1_udp_notraffic_diff_egress_throttle.csv')
	#test6('ub1_udp_notraffic_diff_ingress_throttle.csv')
	#test7('test7.csv')
	#test8('test8_1.csv')
	#test8('test8_2.csv')
	#test8('test8_3.csv')
	#test9('test9.csv')
