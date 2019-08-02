# Mimics the MAS server side script, run with system python

import socket
import os, sys
import time
import errno
import threading

data = []
receiveData = True

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.settimeout(0.01)

host = "127.0.0.1"
port = 23456

server.bind((host, port))
#server.listen()
'''
while True:
	try:
		client, addr = server.accept()
	except socket.error: # Wait for connection
		continue
	break
'''
print("Connected client")
#toSend = ('{{' + 'Awoo' + ':' + False + '}}')
server.sendto("recognizeFace".encode('utf-8'), ("127.0.0.1", 34567))

def comm():
	while receiveData:
		received = None
		try:
			received, addr = server.recvfrom(64)
			received = received.decode('utf-8')
			print("Received: {}\tDataSize: {}".format(received, len(data)))
		except socket.error: # No data received
			pass

		if received != None:
			data.append(received)

	server.close()
	
#thr = threading.Thread(target = comm)
#thr.setDaemon(True)
#thr.start()

comm()