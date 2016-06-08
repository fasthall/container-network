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

	lastRxBytes = {}
	lastTxBytes = {}

	while True:
		time.sleep(2)
		os.system('clear')

		docker_id = subprocess.check_output(['docker', 'ps', '-q']).split('\n')[:-1]
		for cid in docker_id:
			jsonObj = json.loads(subprocess.check_output(['docker', 'inspect', cid]).replace('\n', ' '))[0]
			pid = jsonObj['State']['Pid']
			cname = str(jsonObj['Name'])
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
						downlink = (rxBytes - lastRxBytes[cid]) / 2
						uplink = (txBytes - lastTxBytes[cid]) / 2
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
	
						if len(sys.argv) > 1:	
							es.index(index = 'network-' + str(datetime.datetime.now().date()), doc_type = 'throughput', body = {'Pid': pid, 'Cid': cid, 'Name': cname, 'RxBytes': downlink, 'TxBytes': uplink, 'timestamp': datetime.datetime.utcnow()})
						lastRxBytes[cid] = rxBytes
						lastTxBytes[cid] = txBytes
						print('')
				devfile.close()
			except:
				continue
