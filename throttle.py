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
	else:
		print('Incorrect format.')
		exit()
	urate = sys.argv[3]
	if urate.endswith('k') or urate.endswith('K'):
		urate = urate[:-1]
	elif urate.endswith('m') or urate.endswith('M'):
		urate = urate[:-1] + '000'
	else:
		print('Incorrect format.')
		exit()
	jsonStr = subprocess.check_output('docker inspect ' + cname, shell = True).replace('\n', ' ')
	pid = json.loads(jsonStr)[0]['State']['Pid']

	# link netns namespace
	print("Container's PID: " + str(pid))
	subprocess.check_output('mkdir -p /var/run/netns', shell = True)
	subprocess.check_output('rm /var/run/netns/' + cname, shell = True)
	subprocess.check_output('ln -s /proc/' + str(pid) + '/ns/net /var/run/netns/' + cname, shell = True)
	print('Namespace ' + cname + ' linked.')

	iplink = subprocess.check_output('ip netns exec ' + cname + ' ip link show', shell = True).split('\n')
	for i in iplink:
		s = i.split(':')
		if len(s) > 1 and s[1] == ' eth0':
			vethid = int(s[0]) + 1
	iplink = subprocess.check_output('ip link show', shell = True).split('\n')
	for i in iplink:
		s = i.split(':')
		if len(s) > 1 and s[0] == str(vethid):
			veth = s[1][1:]
	subprocess.check_output('tc qdisc del dev ' + veth + ' root', shell = True)
	subprocess.check_output('tc qdisc add dev ' + veth + ' root tbf rate ' + drate + 'kbit latency 50ms burst ' + str(int(drate) / 2), shell = True)
	subprocess.check_output('ip netns exec ' + cname + ' tc qdisc del dev eth0 root', shell = True)
	subprocess.check_output('ip netns exec ' + cname + ' tc qdisc add dev eth0 root tbf rate ' + urate + 'kbit latency 50ms burst ' + str(int(urate) / 2), shell = True)
	uqdisc = subprocess.check_output('ip netns exec  ' + cname + ' tc qdisc show dev eth0', shell = True).rstrip('\n')
	print('Egress policy')
	print(uqdisc)
	dqdisc = subprocess.check_output('tc qdisc show dev ' + veth, shell = True).rstrip('\n')
	print('Ingress policy')
	print(dqdisc)
