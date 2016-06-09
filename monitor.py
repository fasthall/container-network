import os
import sys
import time
import json
import getopt
import datetime
import elasticsearch
import subprocess

def usage():
	print('Usage:')
	print('python ' + sys.argv[0] + ' [OPTIONS]')
	print('')
	print('Description:')
	print('  Monitor running docker container\'s network bandwidth and report to elasticsearch server.')
	print('')
	print('Options:')
	print('  -e, --elasticsearch   Specify elasticsearch server hostname')
	print('  -f, --frequency       Specify refresh rate in seconds')
	print('  -n, --name            Only monitor the container with given name')
	print('  -h, --help            This page')

if __name__ == "__main__":
	try:
		opts, args = getopt.getopt(sys.argv[1:], 'e:f:n:h', ['elasticsearch', 'frequency', 'name', 'help'])
	except getopt.GetoptError:
		usage()
		exit(2)
	freq = 1
	monitored = []
	for opt, arg in opts:
		if opt in ('-e', '--elasticsearch'):
			host = arg
		elif opt in ('-f', '--frequency'):
			try:
				freq = int(arg)
			except ValueError:
				print('Incorrect refresh rate.')
				exit(2)
		elif opt in ('-n', '--name'):
			monitored.append(arg)
		elif opt in ('-h', '--help'):
			usage()
			exit(2)
		else:
			usage()
			exit(2)
	if 'host' in locals():
		es = elasticsearch.Elasticsearch(host)

	lastRxBytes = {}
	lastTxBytes = {}

	while True:
		os.system('clear')

		docker_id = subprocess.check_output(['docker', 'ps', '-q']).split('\n')[:-1]
		for cid in docker_id:
			jsonObj = json.loads(subprocess.check_output(['docker', 'inspect', cid]).replace('\n', ' '))[0]
			pid = jsonObj['State']['Pid']
			cname = str(jsonObj['Name'][1:])
			if len(monitored) > 0 and cname not in monitored:
				continue
			print('Docker container: ' + cname)

			filename = '/proc/' + str(pid) + '/net/dev'
			try:
				devfile = open(filename, 'r')
				for line in devfile:
					s = line.split()
					if s[0] == 'eth0:':
						rxBytes = float(s[1])
						rxPackets = int(s[2])
						txBytes = float(s[9])
						txPackets = int(s[10])
						if cid not in lastRxBytes:
							lastRxBytes[cid] = rxBytes
						if cid not in lastTxBytes:
							lastTxBytes[cid] = txBytes
						print('Received: ' + str(rxBytes) + ' bytes ' + str(rxPackets) + ' packets')
						print('Sent: ' + str(txBytes) + ' bytes ' + str(txPackets) + ' packets')
						downlink = (rxBytes - lastRxBytes[cid]) / freq
						uplink = (txBytes - lastTxBytes[cid]) / freq
						if downlink < 1024:
							print('Downlink bandwidth: ' + str(downlink) + ' bytes/s')
						elif downlink < 1024 * 1024:
							print('Downlink bandwidth: ' + str(downlink / 1024) + ' kbytes/s')
						else:
							print('Downlink bandwidth: ' + str(downlink / 1024 / 1024) + ' mbytes/s')
						if uplink < 1024:
							print('Uplink bandwidth: ' + str(uplink) + ' bytes/s')
						elif uplink < 1024 * 1024:
							print('Uplink bandwidth: ' + str(uplink / 1024) + ' kbytes/s')
						else:
							print('Uplink bandwidth: ' + str(uplink / 1024 / 1024) + ' mbytes/s')
	
						if 'es' in locals():	
							es.index(index = 'network-' + str(datetime.datetime.now().date()), doc_type = 'throughput', body = {'Pid': pid, 'Cid': cid, 'Name': cname, 'RxBytes': downlink, 'TxBytes': uplink, 'timestamp': datetime.datetime.utcnow()})
						lastRxBytes[cid] = rxBytes
						lastTxBytes[cid] = txBytes
						print('')
				devfile.close()
			except:
				continue
		time.sleep(freq)
