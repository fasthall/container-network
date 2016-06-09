import os
import sys
import time
import json
import getopt
import subprocess

def usage():
	print('Usage: python ' + sys.argv[0] + ' [-f filename]')
	print('')
	print('Options:')
	print('  -f, --file        Read configuration from specified file')
	print('  -h, --help        This page')
	print('')
	print('The content of configuration file should look like this:')
	print('  container_1 weight_1')
	print('  container_2 weight_2')
	print('  ...')
	print('For example, the following configuration will force container c1 use 50% of bandwidth, c2 and c3 share the remaining 50%.')
	print('  c1 2')
	print('  c2 1')
	print('  c3 1')

def reload_config(filename):
	rules = {}
	try:
		conf = open(filename, 'r')
		print('Read configuration from ' + filename)
		for line in conf:
			if line.startswith('#'):
				continue
			rule = line.split(' ')
			cname = rule[0]
			weight = int(rule[1])
			rules[cname] = weight
		for key in rules.keys():
			if rules[key] == 0:
				del rules[key]
		conf.close()
	except IOError:
		print('Cannot open configuration ' + filename)
		exit(2)
	except:
		print('Invalid configuration.')

	return rules;

def link_netns(rules):
	# If the container is not found, it gets removed from the rules
	os.system('sudo mkdir -p /var/run/netns')
	for cid in rules.keys():
		try:
			jsonObj = json.loads(subprocess.check_output(['docker', 'inspect', cid]).replace('\n', ' '))[0]
		except subprocess.CalledProcessError:
			del rules[cid]
			continue
		pid = jsonObj['State']['Pid']
		cname = str(jsonObj['Name'])
		os.system('sudo rm /var/run/netns/' + cname)
		os.system('sudo ln -s /proc/' + str(pid) + '/ns/net /var/run/netns/' + cname)

def cal_bandwidth(lastRxBytes, rules, freq):
	ingress= {}
	for cid in rules:
		print(cid + ' ' + str(rules[cid]))
		jsonObj = json.loads(subprocess.check_output(['docker', 'inspect', cid]).replace('\n', ' '))[0]
		pid = jsonObj['State']['Pid']
		cname = str(jsonObj['Name'])
		filename = '/proc/' + str(pid) + '/net/dev'
		try:
			devfile = open(filename, 'r')
			for line in devfile:
				s = line.split()
				if s[0] == 'eth0:':
					rxBytes = float(s[1])
					if cid not in lastRxBytes:
						lastRxBytes[cid] = rxBytes
					ingress[cid] = (rxBytes - lastRxBytes[cid]) / freq
					lastRxBytes[cid] = rxBytes
					print(str(ingress[cid] / 1024) + 'kbyte/s')
			devfile.close()
		except:
			continue
	return ingress

def get_veth(cname):
	iplink = subprocess.check_output('sudo ip netns exec ' + cname + ' ip link show', shell = True).split('\n')
	for i in iplink:
		s = i.split(':')
		if len(s) > 1 and s[1].startswith(' eth0'):
			vethid = int(s[0]) + 1
	iplink = subprocess.check_output('sudo ip link show', shell = True).split('\n')
	for i in iplink:
		s = i.split(':')
		if len(s) > 1 and s[0] == str(vethid):
			veth = s[1][1:]
			at = veth.find('@')
			if at == -1:
				at = 0
			veth = veth[:at]
	return veth

if __name__ == "__main__":
	try:
		opts, args = getopt.getopt(sys.argv[1:], 'hf:', ['help', 'file='])
	except getopt.GetoptError:
		usage()
		exit(2)
	
	for opt, arg in opts:
		if opt in ('-h', '--help'):
			usage()
			exit(2)
		elif opt in ('-f', '--file'):
			filename = arg
		else:
			usage()
			exit(2)
	if 'filename' not in locals():
		filename = 'weighted.conf'
		print('Didn\'t specify filename, read from weighted.conf.')
	
	rules = reload_config(filename)
	link_netns(rules)
	total_weight = 0
	for key in rules:
		total_weight += rules[key]
	for cid in rules:
		veth = get_veth(cid)
		drate = 1024 * 100 / 8 * rules[cid] / total_weight
		os.system('sudo tc qdisc del dev ' + veth + ' root')
		os.system('sudo tc qdisc add dev ' + veth + ' root tbf rate ' + str(drate * 8) + 'kbit latency 50ms burst ' + str(drate * 8 * 4))	
