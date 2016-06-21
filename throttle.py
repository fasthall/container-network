import os
import sys
import json
import getopt
import subprocess

def usage():
	print('Usage: python ' + sys.argv[0] + ' CONTAINER_NAME [OPTIONS]')
	print('')
	print('Description:')
	print('  Set the download or upload speed limit of a container using tc and container\'s network namespace.')
	print('')
	print('Options:')
	print('  -d, --download    #kmKM        Set download speed limit in specified unit')
	print('  -u, --upload      #kmKM        Set upload speed limit in specified unit')
	print('  -c, --clean                    Clean the speed limits')
	print('  -q, --quiet                    Don\'t show message')
	print('  -h, --help                     This page')

def arg_to_rate(arg):
	try:
		if arg.endswith('k'):
			rate = float(arg[:-1]) * 1000
		elif arg.endswith('K'):
			rate = float(arg[:-1]) * 1024
		elif arg.endswith('m'):
			rate = float(arg[:-1]) * 1000000
		elif arg.endswith('M'):
			rate = float(arg[:-1]) * 1024 * 1024
		else:
			print('Incorrect speed format.')
			exit(2)
		if rate == 0:
			print('Incorrect speed format.')
			exit(2)
	except ValueError:
		print('Incorrect speed format.')
		exit(2)

	return rate

def get_veth(cname):
	try:
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
	except subprocess.CalledProcessError:
		print('Container ' + cname + ' doesn\'t exist.')
		exit(2)

def throttle(argv):
	quiet = False
	if len(argv) < 2:
		usage()
		exit(2)
	cname = argv[1]
	if cname == '-h' or cname == '--help':
		usage()
		exit(2)

	opts, args = getopt.getopt(argv[2:], 'd:u:cqh', ['download=', 'upload=', 'clean', 'quiet', 'help'])
	for opt, arg in opts:
		if opt in ('-h', '--help'):
			usage()
			exit(2)
		elif opt in ('-q', '--quiet'):
			quiet = True
		elif opt in ('-d', '--download'):
			drate = arg_to_rate(arg)
		elif opt in ('-u', '--upload'):
			urate = arg_to_rate(arg)
		elif opt in ('-c', '--clean'):
			veth = get_veth(cname)
			os.system('sudo tc qdisc del dev ' + veth + ' root')
			os.system('sudo ip netns exec ' + cname + ' tc qdisc del dev eth0 root')
			print('Throttle rules cleaned.')
			exit(0)
		else:
			usage()
			exit(2)
	if 'drate' not in locals() and 'urate' not in locals():
		print('At least one of download speed or upload speed needs to be specified.')
		exit(2)
	try:
		jsonStr = subprocess.check_output('docker inspect ' + cname, shell = True).replace('\n', ' ')
	except subprocess.CalledProcessError:
		print('Container ' + cname + ' doesn\'t exist')
		exit(2)
	jsonObj = json.loads(jsonStr)[0]
	pid = jsonObj['State']['Pid']
	cname = str(jsonObj['Name'][1:])

	# link netns namespace
	#print("Container's PID: " + str(pid))
	os.system('sudo mkdir -p /var/run/netns')
	os.system('sudo rm /var/run/netns/' + cname)
	os.system('sudo ln -s /proc/' + str(pid) + '/ns/net /var/run/netns/' + cname)
	#print('Namespace ' + cname + ' linked.')
	
	veth = get_veth(cname)
	os.system('sudo tc qdisc del dev ' + veth + ' root')
	if 'drate' in locals():
		os.system('sudo tc qdisc add dev ' + veth + ' root tbf rate ' + str(drate * 8) + 'bit latency 50ms burst ' + str(drate * 8 / 250))
	os.system('sudo ip netns exec ' + cname + ' tc qdisc del dev eth0 root')
	if 'urate' in locals():
		os.system('sudo ip netns exec ' + cname + ' tc qdisc add dev eth0 root tbf rate ' + str(urate * 8) + 'bit latency 50ms burst ' + str(urate * 8 / 250))
	uqdisc = subprocess.check_output('sudo ip netns exec  ' + cname + ' tc qdisc show dev eth0', shell = True).rstrip('\n')
	if not quiet:
		print('Egress policy')
		print(uqdisc)
	dqdisc = subprocess.check_output('sudo tc qdisc show dev ' + veth, shell = True).rstrip('\n')
	if not quiet:
		print('Ingress policy')
		print(dqdisc)

if __name__ == "__main__":
	throttle(sys.argv)
