#Mimics the MAS server side script, run with system python

import socket
import os, sys
import time
import errno
import threading

data = []

server = socket.socket()
host = socket.gethostname()
port = 12345
server.settimeout(10)
server.bind((host, port))
server.listen(5)
client, addr = server.accept()
client.setblocking(True)
client.settimeout(5)
#if additionFirstRun("Super Experimental Additions"):
#client.sendall("first".encode('utf-8'))
#client.sendall("recognizeFace".encode('utf-8'))

def comm():
	while True:
		try:
			received = client.recv(1024).decode('utf-8')
			if received is not None:
				data.append(received)
				print("Received: {}\nDataSize: {}".format(received, len(data)))
		except:
			pass

	client.close()
	server.close()
	
#thr = threading.Thread(target = comm)
#thr.setDaemon(True)
#thr.start()

comm()