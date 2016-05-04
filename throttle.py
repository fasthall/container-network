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
	jsonStr = subprocess.check_output(['docker', 'inspect', cname]).replace('\n', ' ')
	pid = json.loads(jsonStr)[0]['State']['Pid']

	# link netns namespace
	print(pid)
	os.system('mkdir -p /var/run/netns')
	os.system('rm /var/run/netns/' + cname)
	os.system('ln -s /proc/' + str(pid) + '/ns/net /var/run/netns/' + cname)

	iplink = subprocess.check_output(['ip', 'netns', 'exec', cname, 'ip', 'link', 'show']).split('\n')
	for i in iplink:
		s = i.split(':')
		if len(s) > 1 and s[1] == ' eth0':
			vethid = int(s[0]) + 1
	iplink = subprocess.check_output(['ip', 'link', 'show']).split('\n')
	for i in iplink:
		s = i.split(':')
		if len(s) > 1 and s[0] == str(vethid):
			veth = s[1][1:]
	os.system('tc qdisc del dev ' + veth + ' root')
	os.system('tc qdisc add dev ' + veth + ' root tbf rate ' + drate + 'kbit latency 50ms burst ' + str(int(drate) / 2))
	os.system('ip netns exec ' + cname + ' tc qdisc del dev eth0 root')
	os.system('ip netns exec ' + cname + ' tc qdisc add dev eth0 root tbf rate ' + urate + 'kbit latency 50ms burst ' + str(int(urate) / 2))

