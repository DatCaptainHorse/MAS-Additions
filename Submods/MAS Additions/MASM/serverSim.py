# Mimics the MAS server side script, run with system python

import socket
import os, sys
import time
import json
import errno
import threading

receiveData = True

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.settimeout(0.1) # Blocks
server.bind(("127.0.0.1", 24488))

time.sleep(1)

toSend = json.dumps(("FDAR_TIMEOUT", 15))
server.sendto(toSend.encode("utf-8"), ("127.0.0.1", 24489))
toSend = json.dumps(("FDAR_SETDATASIZE", 100))
server.sendto(toSend.encode("utf-8"), ("127.0.0.1", 24489))
toSend = json.dumps(("FDAR_DETECTIONMETHOD", "HAAR"))
server.sendto(toSend.encode("utf-8"), ("127.0.0.1", 24489))
toSend = json.dumps(("FDAR_ALLOWACCESS", True))
server.sendto(toSend.encode("utf-8"), ("127.0.0.1", 24489))

time.sleep(1)

#toSend = json.dumps(("FDAR_RETAKEDATA", True))
#server.sendto(toSend.encode("utf-8"), ("127.0.0.1", 24489))

time.sleep(5)

toSend = json.dumps(("FDAR_RECOGNIZEONCE", "Player"))
server.sendto(toSend.encode("utf-8"), ("127.0.0.1", 24489))

def comm():
	while receiveData:
		try:
			recv, addr = server.recvfrom(256)
			received = json.loads(recv.decode("utf-8"))
			if received is not None:
				print(f"Received: {received}")
		except socket.timeout: # Ignore
			pass
		except socket.error as e:
			print(f"Socket error: {e}")
	server.close()
comm()