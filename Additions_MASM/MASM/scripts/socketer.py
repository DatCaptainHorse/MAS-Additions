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
	
		client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		client.bind(("127.0.0.1", 23456))
		#client.setblocking(False)
		client.settimeout(0.01)

		#host = socket.gethostname() # TCP
		''' # TCP
		while True:
			try:
				client.connect((host, port))
			except socket.error: # Wait for connection
				continue
			break
		'''
		SE.Log("Connected!\n")
		execs = 0

def receiveData():
	global client
	global data
	global execs
	if client != None:
		try:
			dat, addr = client.recvfrom(64)
			if dat != None:
				dat = dat.decode('utf-8')
				SE.Log("received: {}".format(dat))
				data.append(dat)
		except socket.error: # No data
			pass
		
		if hasData("first"):
			SE.Log("\nWhats this? How interesting..\n")

def sendData(toSend):
	global client
	if client != None:
		client.sendto(toSend.encode('utf-8'), ("127.0.0.1", 12345))
			
def Start():
	connectMAS()

def Render():
	receiveData()