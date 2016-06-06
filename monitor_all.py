import os
import sys
import time
import datetime
import elasticsearch
import subprocess
import json

if __name__ == "__main__":
	if len(sys.argv) < 1:
		print('Usage:')
		print('python monitor.py [elasticsearch host]')
		sys.exit()
	
	if len(sys.argv) > 1:
		es = elasticsearch.Elasticsearch(sys.argv[1])

	while True:
		time.sleep(1)
		os.system('clear')

		docker_id = subprocess.check_output(['docker', 'ps', '-aq']).split('\n')[:-1]
		for i in docker_id:
			jsonObj = json.loads(subprocess.check_output(['docker', 'inspect', i]).replace('\n', ' '))[0]
			pid = jsonObj['State']['Pid']
			cname = str(jsonObj['Name'])
			print('Docker container: ' + cname)

			filename = '/proc/' + str(pid) + '/net/dev'
			devfile = open(filename, 'r')
			devfile.readline()
			devfile.readline()
			s = devfile.readline().split()
			lastRxBytes = float(s[1])
			lastTxBytes = float(s[9])
	
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
