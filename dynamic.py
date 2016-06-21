import os
import time
import json
import subprocess
from throttle import *

max_credit = 1024 * 1024 * 10 # maximum capacity in bytes
min_credit = 0
containers = []
credits = {}
lasts = {}
busy_weights = {}
free_credit = 0

def update_containers():
	global containers
	containers = subprocess.check_output(['docker', 'ps', '-q']).split('\n')[:-1]
	#print(containers)

def update_throttle(cid):
	global credits
	credit = credits[cid][0]
	print(cid + ': ' + str(credit))
	cmd = ['dynamic', cid, '-d', str(credit / 1024) + 'k', '-q']
	throttle(cmd)

def update_credits():
	global containers
	global credits
	global min_credit
	global busy_weights
	global free_credit
	print('Free: ' + str(free_credit))
	container_num = len(containers)
	min_credit = max_credit / container_num
	for cid in containers:
		if cid in busy_weights:
			extra = free_credit * busy_weights[cid]
		else:
			extra = 0
		credits[cid] = [min_credit + extra, time.time()]

def allocate_free_credit(free_credit, busy_containers, busy_weights):
	for cid in busy_containers:
		credits[cid][0] += free_credit * busy_weights[cid]

def get_bytes(cid):
	jsonObj = json.loads(subprocess.check_output(['docker', 'inspect', cid]).replace('\n', ' '))[0]
	pid = jsonObj['State']['Pid']
	filename = '/proc/' + str(pid) + '/net/dev'
	try:
		devfile = open(filename, 'r')
		for line in devfile:
			s = line.split()
			if s[0] == 'eth0:':
				rxBytes = int(s[1])
				txBytes = int(s[9])
				break
		devfile.close()
		return (rxBytes, txBytes)
	except:
		pass

def get_remaining_credit(cid):
	return credits[cid][0]

def get_depleting_time(cid):
	now = time.time()
	return now - credits[cid][1]

def calc_new_credit(cid, depleting_time):
	pass

if __name__ == '__main__':
	# get container list and allocate credits
	update_containers()
	update_credits()
	for cid in containers:
		lasts[cid] = get_bytes(cid)

	while True:
		time.sleep(1)
		os.system('clear')

		update_containers()
		update_credits()

		busy_weights = {}
		free_credit = 0
		for cid in containers:
			update_throttle(cid)
			print('Container ' + cid)

			# update credit usages
			(rx, tx) = get_bytes(cid)
			crx = rx -lasts[cid][0]
			ctx = tx - lasts[cid][1]
			print('rx: ' + str(crx) + '\ntx: ' + str(ctx))
			lasts[cid] = (rx, tx)
			#credits[cid][0] -= crx

			# check usage
			#remaining = get_remaining_credit(cid)
			remaining = min_credit - crx
			print('Remaining credit: ' + str(remaining))
			if remaining <= 0:
				depleting_time = get_depleting_time(cid)
				busy_weights[cid] = remaining
				new_credit = calc_new_credit(cid, depleting_time)
			else:
				free_credit += remaining
				busy_weights[cid] = 0

		# calculate bandwidth weights
		sum_remaining = sum(busy_weights.values())
		if sum_remaining != 0:
			for k in busy_weights.keys():
				busy_weights[k] = float(busy_weights[k]) / sum_remaining

		print('')
