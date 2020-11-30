# Using sockets to transfer data between Ren'Py and MASM
import socket
import re

client = None
data = []
dictData = {}
execs = 0

def dictHas(dictKey):
	dictData.get(dictKey, False)

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
		client.bind(("127.0.0.1", 24489))
		client.settimeout(0.1)
		
		SE.Log("Connected!\n")
		execs = 0

def str2bool(v):
  return str(v).lower() in ("True", "true", "1")

def receiveData():
	global client
	global data
	global execs

	if client != None:
		try:
			dat, addr = client.recvfrom(128)

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
		client.sendto(toSend.encode('utf-8'), ("127.0.0.1", 24488))

def sendData(toSend):
	global client
	if client != None:
		client.sendto(toSend.encode('utf-8'), ("127.0.0.1", 24488))
			
def Start():
	connectMAS()

def Render():
	receiveData()