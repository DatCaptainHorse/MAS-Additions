# Mimics the MAS server side script, run with system python

import socket
import os, sys
import time
import errno
import threading

data = []
receiveData = True

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.settimeout(0.1) # Blocks for 0.1s
server.bind(("127.0.0.1", 24488))

#toSend = ('{{' + 'Awoo' + ':' + 'False' + '}}')
#server.sendto(toSend.encode('utf-8'), ("127.0.0.1", 24489))
#server.sendto("recognizeFace.DNN".encode('utf-8'), ("127.0.0.1", 24489))
server.sendto("ping".encode('utf-8'), ("127.0.0.1", 24489))

def comm():
	while receiveData:
		received = None
		try:
			received, addr = server.recvfrom(128)
			received = received.decode('utf-8')
			print(f"Received: {received}")
		except socket.error: # Ignore
			pass
		if received != None:
			data.append(received)
			break
	server.close()
comm()