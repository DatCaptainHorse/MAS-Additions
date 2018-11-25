# Using sockets to transfer data between Ren'Py and MASM
import socket

client = None
data = []
execs = 0

def hasData(dat):
	global data
	if dat in data:
		data.remove(dat)
		return True
	else:
		return False

def connectMAS():
	global client
	global data

	if client == None:
		SE.Log("\nConnecting to MAS..")
	
		client = socket.socket()
		#client.setblocking(False)
		client.settimeout(0.1)

		host = socket.gethostname()
		port = 12345

		while True:
			try:
				client.connect((host, port))
			except socket.error: # Wait for connection
				continue
			break
			
		SE.Log("Connected!\n")
		execs = 0

def receiveData():
	global client
	global data
	global execs
	
	if client != None:
		if execs >= 5:
			SE.Log("Too many exceptions, attempting to reconnect..")
			client.close()
			client = None
			connectMAS()

		try:
			dat = client.recv(64).decode('utf-8')
			if dat != None:
				data.append(dat)
		except socket.timeout: # No data
			pass
		
		if hasData("first"):
			SE.Log("\nWhats this? How interesting..\n")
			
def sendData(toSend):
	global client
	if client != None:
		client.sendall(toSend.encode('utf-8'))
			
def Start():
	connectMAS()

def Update():
	receiveData()