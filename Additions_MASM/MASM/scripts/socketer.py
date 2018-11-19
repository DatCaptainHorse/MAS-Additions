import socket

client = None
data = None
execs = 0

def connectMAS():
	global client
	global data
	
	if client is None:
		SE.Log("\nConnecting to MAS..")
	
		client = socket.socket()
		host = socket.gethostname()
		port = 12345
		
		# Using sockets to transfer data between Ren'Py and MASM
		try:
			client.connect((host, port))
		except Exception as exc:
			SE.Log("Failed to connect: ", exc)
			return
			
		SE.Log("Connected!\n")
		execs = 0

def receiveData():
	global client
	global data
	global execs
	
	if client is not None:
		if execs >= 5:
			SE.Log("Too many exceptions, attempting to reconnect..")
			client.close()
			client = None
			connectMAS()

		try:
			data = client.recv(64).decode('utf-8')
		except:
			SE.Log("Exception getting data")
			execs += 1
			return
		
		if data is not None and data == 'first':
			SE.Log("\nWhats this? How interesting..\n")
			
def sendData(toSend):
	global client
	if client is not None:
		client.sendall(toSend.encode('utf-8'))
			
def Start():
	connectMAS()

def Update():
	receiveData()