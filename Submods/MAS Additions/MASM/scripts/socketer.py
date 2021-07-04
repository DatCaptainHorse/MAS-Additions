# Using sockets to transfer data between Ren'Py and MASM
# TODO: Ping-Pong alive check messages
import re
import time
import socket
import threading

data = []
dictData = {}
socketUDP = None
commThread = None
commRun = threading.Event()
commLock = threading.Lock()

def connectMAS():
	global data
	global socketUDP
	if not socketUDP:
		SE.Log("Creating socket..")
		socketUDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		socketUDP.settimeout(0.1)
		socketUDP.bind(("127.0.0.1", 24489))
		SE.Log("Done")
		execs = 0

def receiveData():
	global data
	global commRun
	global dictData
	global commLock
	global socketUDP
	while not commRun.is_set():
		received = None
		try:
			recv, addr = socketUDP.recvfrom(128)
			received = recv.decode("utf-8")
		except socket.timeout:
			pass # No data
		except socket.error as e:
			SE.Log(f"socketer socket error : {str(e)}")
			pass # Log but pass

		if received:
			print(f"Received: {received}")
			commLock.acquire()
			if received.startswith('{{'):
				res = re.search("{{(.*):(.*)}}", received)
				dictData[res.group(1)] = res.group(2).lower() in ("True", "true", "1")
			elif received != "ping":
				if received in data:
					data.remove(received)
				data.append(received)
			else:
				sendData("pong")
			commLock.release()
		else:
			commLock.acquire()
			if len(data) >= 16:
				data.pop()
			commLock.release()
			time.sleep(0.01) # Ease up on the CPU

def dictSend(sendKey, sendVal):
	global commRun
	global commLock
	global dictData
	global socketUDP
	if socketUDP and not commRun.is_set():
		commLock.acquire()
		dictData[sendKey] = sendVal
		commLock.release()
		toSend = ("{{" + sendKey + ":" + sendVal + "}}")
		socketUDP.sendto(toSend.encode("utf-8"), ("127.0.0.1", 24488))

def sendData(toSend):
	global socketUDP
	if socketUDP:
		socketUDP.sendto(toSend.encode("utf-8"), ("127.0.0.1", 24488))

def dictHas(dictKey):
	global commRun
	global commLock
	global dictData
	res = False
	if not commRun.is_set():
		commLock.acquire()
		res = dictData.get(dictKey, False)
		commLock.release()
	return res

def hasData(dat):
	global data
	global commRun
	global commLock
	res = False
	if not commRun.is_set():
		commLock.acquire()
		if dat in data:
			data.remove(dat)
			res = True
		commLock.release()
	return res

def hasDataWith(dat):
	global data
	global commRun
	global commLock
	res = None
	if not commRun.is_set():
		commLock.acquire()
		for fDat in data:
			if dat in fDat:
				data.remove(fDat)
				res = fDat
		commLock.release()
	return res

def Start():
	global commThread
	connectMAS()
	commThread = threading.Thread(target = receiveData)
	commThread.start()

def OnQuit():
	global commRun
	global commThread
	commRun.set()
	commThread.join()