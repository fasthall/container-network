import os
import sys
import time
import datetime
import elasticsearch
import subprocess
import json

if __name__ == "__main__":
	if len(sys.argv) < 2:
		print('Usage:')
		print('python monitor.py container_name [elasticsearch host]')
		sys.exit()
	
	if len(sys.argv) > 2:
		es = elasticsearch.Elasticsearch(sys.argv[2])
	cname = sys.argv[1]
	jsonStr = subprocess.check_output(['docker', 'inspect', cname]).replace('\n', ' ')
	pid = json.loads(jsonStr)[0]['State']['Pid']
	filename = '/proc/' + str(pid) + '/net/dev'
	devfile = open(filename, 'r')
	devfile.readline()
	devfile.readline()
	s = devfile.readline().split()
	lastRxBytes = float(s[1])
	lastTxBytes = float(s[9])

	while True:
		time.sleep(1)
		os.system('clear')
		devfile.seek(0)
		for line in devfile:
			s = line.split()
			if s[0] == 'eth0:':
				rxBytes = float(s[1])
				rxPackets = float(s[2])
				txBytes = float(s[9])
				txPackets = float(s[10])
				print('Received: ' + str(rxBytes) + ' bytes ' + str(rxPackets) + ' packets')
				print('Sent: ' + str(txBytes) + ' bytes ' + str(txPackets) + ' packets')
				downlink = rxBytes - lastRxBytes
				uplink = txBytes - lastTxBytes
				if downlink < 1024:
					print('Downlink bandwidth: ' + str(downlink) + ' bytes/s')
				elif downlink < 1024 * 1024:
					print('Downlink bandwidth: ' + str(downlink / 1024) + ' kbytes/s')
				elif downlink < 1024 * 1024 * 1024:
					print('Downlink bandwidth: ' + str(downlink / 1024 / 1024) + ' mbytes/s')
				if uplink < 1024:
					print('Uplink bandwidth: ' + str(uplink) + ' bytes/s')
				elif uplink < 1024 * 1024:
					print('Uplink bandwidth: ' + str(uplink / 1024) + ' kbytes/s')
				elif uplink < 1024 * 1024 * 1024:
					print('Uplink bandwidth: ' + str(uplink / 1024 / 1024) + ' mbytes/s')
				
				if len(sys.argv) > 2:	
					es.index(index = 'network-' + str(datetime.datetime.now().date()), doc_type = 'throughput', body = {'Name': cname, 'RxBytes': downlink, 'TxBytes': uplink, 'timestamp': datetime.datetime.now()})
				lastRxBytes = rxBytes
				lastTxBytes = txBytes
