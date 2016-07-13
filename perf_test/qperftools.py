import sys
import subprocess

def nat_tcp(host, cnt):
	cmd = ['qperf', host]
	for i in range(cnt):
		cmd.append('tcp_lat')
	result = subprocess.check_output(' '.join(cmd), shell = True).split('\n')
	ttl = 0
	for i in range(1, len(result), 2):
		lat = result[i][16:-3]
		ttl += float(lat)
	return ttl / cnt

def nat_udp(host, cnt):
	cmd = ['qperf', host]
	for i in range(cnt):
		cmd.append('udp_lat')
	result = subprocess.check_output(' '.join(cmd), shell = True).split('\n')
	ttl = 0
	for i in range(1, len(result), 2):
		lat = result[i][16:-3]
		ttl += float(lat)
	return ttl / cnt

def tcp(cname, host, cnt):
	cmd = ['docker', 'exec', cname, 'qperf', host]
	for i in range(cnt):
		cmd.append('tcp_lat')
	result = subprocess.check_output(' '.join(cmd), shell = True).split('\n')
	ttl = 0
	for i in range(1, len(result), 2):
		lat = result[i][16:-3]
		ttl += float(lat)
	return ttl / cnt

def udp(cname, host, cnt):
	cmd = ['docker', 'exec', cname, 'qperf', host]
	for i in range(cnt):
		cmd.append('udp_lat')
	result = subprocess.check_output(' '.join(cmd), shell = True).split('\n')
	ttl = 0
	for i in range(1, len(result), 2):
		lat = result[i][16:-3]
		ttl += float(lat)
	return ttl / cnt

def tcp_bw(cname, host):
	cmd = 'docker exec ' + cname + ' qperf ' + host + ' tcp_bw'
	result = subprocess.check_output(cmd, shell = True).split('\n')
	return result[1][11:-4]
