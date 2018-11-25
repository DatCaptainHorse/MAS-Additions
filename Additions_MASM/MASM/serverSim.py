# Mimics the MAS server side script, run with system python

import socket
import os, sys
import time
import errno
import threading

data = []
receiveData = True

server = socket.socket()
server.settimeout(0.1)

host = socket.gethostname()
port = 12345

server.bind((host, port))
server.listen()

while True:
	try:
		client, addr = server.accept()
	except socket.error: # Wait for connection
		continue
	break

client.sendall("recognizeFace".encode('utf-8'))

def comm():
	while receiveData:
		received = None
		try:
			received = client.recv(64).decode('utf-8')
		except socket.timeout: # No data received
			pass

		if received != None:
			data.append(received)
			print("Received: {}\tDataSize: {}".format(received, len(data)), end='\r')

	client.close()
	server.close()
	
#thr = threading.Thread(target = comm)
#thr.setDaemon(True)
#thr.start()

comm()