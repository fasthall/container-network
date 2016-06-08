import os
import subprocess
import time
import json

def reload_config():
	rules = {}
	for key in rules:
		rules[key] = 0
	try:
		conf = open('config', 'r')
	except:
		print('Cannot open config file')
		exit(0)
	for line in conf:
		rule = line.split(' ')
		cname = rule[0]
		weight = int(rule[1])
		rules[cname] = weight
	for key in rules.keys():
		if rules[key] == 0:
			del rules[key]
	conf.close()
	return rules;

def link_netns(rules):
	for cid in rules:
		jsonObj = json.loads(subprocess.check_output(['docker', 'inspect', cid]).replace('\n', ' '))[0]
		pid = jsonObj['State']['Pid']
		cname = str(jsonObj['Name'])
		os.system('sudo rm /var/run/netns/' + cname)
		os.system('sudo ln -s /proc/' + str(pid) + '/ns/net /var/run/netns/' + cname)

def cal_bandwidth(lastRxBytes, rules):
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
					ingress[cid] = (rxBytes - lastRxBytes[cid]) / 5
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
	os.system('sudo mkdir -p /var/run/netns')
	#lastRxBytes = {}
	#while True:
	rules = reload_config()
	link_netns(rules)
	total_weight = 0
	for key in rules:
		total_weight += rules[key]
	#ingress = cal_bandwidth(lastRxBytes, rules)
	#total_ingress = 0
	#for key in ingress:
	#	total_ingress += ingress[key]
	#print('total: ' + str(total_ingress / 1024) + 'kbytes/s')
	for cid in rules:
		veth = get_veth(cid)
		drate = 1024 * 100 / 8 * rules[cid] / total_weight
		#print(cid + ': ' + str(drate) + 'kbytes/s')
		os.system('sudo tc qdisc del dev ' + veth + ' root')
		os.system('sudo tc qdisc add dev ' + veth + ' root tbf rate ' + str(drate * 8) + 'kbit latency 50ms burst ' + str(drate * 8 * 4))	
