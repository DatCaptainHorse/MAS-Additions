# Using sockets to transfer data between Ren'Py and MASM
# TODO: Ping-Pong alive check messages
import re
import time
import json
import errno
import socket
import threading

data = {}
commThread = None
serverSocket = None
commRun = threading.Event()
commLock = threading.Lock()

def connectMAS():
	global data
	global serverSocket
	if serverSocket is None:
		try:
			SE.Log("Creating server socket..")
			serverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			serverSocket.settimeout(0.1)
			serverSocket.bind(("127.0.0.1", 24489))
			SE.Log("Done, sending ready message..")
			serverSocket.sendto(json.dumps(("MASM_READY", True)).encode("utf-8"), ("127.0.0.1", 24488))
			SE.Log("Done")
		except Exception as e:
			SE.Log(f"Creating socket exception: {e}")

def _receiveData():
	global data
	global commRun
	global commLock
	global serverSocket
	while not commRun.is_set():
		try:
			recv, addr = serverSocket.recvfrom(256)
			if recv is not None:
				recv = json.loads(recv.decode("utf-8"))
				SE.Log(f"Received: {recv}")
				if recv[0] == "ping":
					sendData("pong")
				else:
					with commLock:
						data[recv[0]] = recv[1]
		except socket.timeout:
			continue # No data
		except socket.error as e:
			SE.Log(f"Socket receive error: {e}") # Log but pass
		except Exception as e:
			SE.Log(f"Socketer socket exception: {e}")

def sendData(sendKey, sendValue = True):
	global serverSocket
	if serverSocket is not None:
		#SE.Log(f"Sending: {sendKey}")
		serverSocket.sendto(json.dumps((sendKey, sendValue)).encode("utf-8"), ("127.0.0.1", 24488))

def hasDataWith(dictKey):
	global data
	global commLock
	res = None
	with commLock:
		try:
			res = next(((k, v) for k, v in data.items() if k.startswith(dictKey)), None)
			if res[0] is not None:
				del data[res[0]]
		except:
			res = (None, None)
	return res

def hasDataValue(dictKey):
	global data
	global commLock
	res = None
	with commLock:
		res = data.get(dictKey, None)
		if res is not None:
			del data[dictKey]
	return res

def hasDataBool(dictKey):
	global data
	global commLock
	res = False
	with commLock:
		if dictKey in data:
			res = True
			del data[dictKey]
	return res

def Start():
	global commThread
	connectMAS()
	commThread = threading.Thread(target = _receiveData)
	commThread.start()

def OnQuit():
	global commRun
	global commThread
	global serverSocket
	commRun.set()
	commThread.join()
	serverSocket = None