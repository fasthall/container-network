import os
import sys
import json
import subprocess

if __name__ == "__main__":
	cname = sys.argv[1]
	drate = sys.argv[2]
	if drate.endswith('k') or drate.endswith('K'):
		drate = drate[:-1]
	elif drate.endswith('m') or drate.endswith('M'):
		drate = drate[:-1] + '000'
	elif drate != '0':
		print('Incorrect format.')
		exit()
	urate = sys.argv[3]
	if urate.endswith('k') or urate.endswith('K'):
		urate = urate[:-1]
	elif urate.endswith('m') or urate.endswith('M'):
		urate = urate[:-1] + '000'
	elif urate != '0':
		print('Incorrect format.')
		exit()
	jsonStr = subprocess.check_output('docker inspect ' + cname, shell = True).replace('\n', ' ')
	pid = json.loads(jsonStr)[0]['State']['Pid']

	# link netns namespace
	print("Container's PID: " + str(pid))
	os.system('sudo mkdir -p /var/run/netns')
	os.system('sudo rm /var/run/netns/' + cname)
	os.system('sudo ln -s /proc/' + str(pid) + '/ns/net /var/run/netns/' + cname)
	print('Namespace ' + cname + ' linked.')

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
	os.system('sudo tc qdisc del dev ' + veth + ' root')
	if drate != '0':
		os.system('sudo tc qdisc add dev ' + veth + ' root tbf rate ' + drate + 'kbit latency 50ms burst ' + str(int(drate) * 4))
	os.system('sudo ip netns exec ' + cname + ' tc qdisc del dev eth0 root')
	if urate != '0':
		os.system('sudo ip netns exec ' + cname + ' tc qdisc add dev eth0 root tbf rate ' + urate + 'kbit latency 50ms burst ' + str(int(urate) * 4))
	uqdisc = subprocess.check_output('sudo ip netns exec  ' + cname + ' tc qdisc show dev eth0', shell = True).rstrip('\n')
	print('Egress policy')
	print(uqdisc)
	dqdisc = subprocess.check_output('sudo tc qdisc show dev ' + veth, shell = True).rstrip('\n')
	print('Ingress policy')
	print(dqdisc)
