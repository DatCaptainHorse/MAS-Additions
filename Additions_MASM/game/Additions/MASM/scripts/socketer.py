# Using sockets to transfer data between Ren'Py and MASM
import socket
import re

client = None
data = []
dictData = {}
execs = 0
useUDP = False

def dictHas(dictKey):
	dictData.get(dictKey, False)

def hasData(dat):
	global data
	if dat in data:
		data.remove(dat)
		return True
	else:
		return False

def connectMAS(UDPmode):
	global client
	global data
	global useUDP

	useUDP = UDPmode

	if client == None:
		SE.Log("\nConnecting to MAS..")
	
		if useUDP:
			client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			client.bind(("127.0.0.1", 34567))
			client.settimeout(0.01)
		else:
			client = socket.socket()
			client.settimeout(0.01)
			while True:
				try:
					client.connect(("127.0.0.1", 12345))
				except socket.error: # Wait for connection
					continue
				break
		
		SE.Log("Connected!\n")
		execs = 0

def str2bool(v):
  return str(v).lower() in ("True", "true", "1")

def receiveData():
	global client
	global data
	global execs
	global useUDP

	if client != None:
		try:
			if useUDP:
				dat, addr = client.recvfrom(128)
			else:
				dat = client.recv(128)

			if dat != None:
				dat = dat.decode('utf-8')
				SE.Log("received: {}".format(dat))
				if dat.startswith('{{'):
					res = re.search("{{(.*) : (.*)}}", dat)
					dictData[res.group(1)] = str2bool(res.group(2))
					print(dictData)
				else:
					data.append(dat)
		except socket.timeout: # No data
			pass
		
		if hasData("first"):
			SE.Log("\nWhats this? How interesting..\n")

def dictSend(sendKey, sendVal):
	dictData[sendKey] = sendVal
	toSend = ('{{' + sendKey + ':' + sendVal + '}}')
	if client != None:
		if useUDP:
			client.sendto(toSend.encode('utf-8'), ("127.0.0.1", 23456))
		else:
			client.sendall(toSend.encode('utf-8'))

def sendData(toSend):
	global client
	global useUDP
	if client != None:
		if useUDP:
			client.sendto(toSend.encode('utf-8'), ("127.0.0.1", 23456))
		else:
			client.sendall(toSend.encode('utf-8'))
			
def Start():
	connectMAS(True)

def Render():
	receiveData()