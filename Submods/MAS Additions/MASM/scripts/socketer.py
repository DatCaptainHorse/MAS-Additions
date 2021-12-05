# Using sockets to transfer data between Ren'Py and MASM
# TODO: Ping-Pong alive check messages
import json
import socket
import threading

class MASM:
	data = {}
	commThread = None
	serverSocket = None
	commRun = threading.Event()
	commLock = threading.Lock()

	@staticmethod
	def _startThread():
		MASM._connectMAS()
		MASM.commThread = threading.Thread(target = MASM._receiveData)
		MASM.commThread.start()
	
	@staticmethod
	def _stopAll():
		MASM.commRun.set()
		MASM.commThread.join()
		MASM.serverSocket.close()

	@staticmethod
	def _connectMAS():
		if MASM.serverSocket is None:
			try:
				print("Creating server socket..", end=" ")
				MASM.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
				MASM.serverSocket.settimeout(0.1)
				MASM.serverSocket.bind(("127.0.0.1", 24489))
				print("Done")
				print("Sending ready message..", end=" ")
				MASM.sendData("MASM_READY", True)
				print("Done")
			except Exception as e:
				print(f"Creating socket exception: {e}")

	@staticmethod
	def _receiveData():
		while not MASM.commRun.is_set():
			try:
				recv, addr = MASM.serverSocket.recvfrom(256)
				if recv is not None:
					recv = json.loads(recv.decode("utf-8"))
					print(f"Received: {recv}")
					if recv[0] == "ping":
						MASM.sendData("pong")
					else:
						with MASM.commLock:
							MASM.data[recv[0]] = recv[1]
			except socket.timeout:
				continue # No data
			except socket.error as e:
				print(f"Socket receive error: {e}") # Log but pass
			except Exception as e:
				print(f"Socketer socket exception: {e}")

	@staticmethod
	def sendData(sendKey, sendValue = True):
		if MASM.serverSocket is not None:
			#print(f"Sending: {sendKey}")
			MASM.serverSocket.sendto(json.dumps((sendKey, sendValue)).encode("utf-8"), ("127.0.0.1", 24488))

	@staticmethod
	def hasDataWith(dictKey):
		res = None
		with MASM.commLock:
			try:
				res = next(((k, v) for k, v in MASM.data.items() if k.startswith(dictKey)), None)
				if res[0] is not None:
					del MASM.data[res[0]]
			except:
				res = (None, None)
		return res

	@staticmethod
	def hasDataValue(dictKey, defaultValue = None):
		res = defaultValue
		with MASM.commLock:
			got = MASM.data.get(dictKey, None)
			if got is not None:
				res = got
				del MASM.data[dictKey]
		return res

	@staticmethod
	def hasDataBool(dictKey):
		res = False
		with MASM.commLock:
			if dictKey in MASM.data:
				res = True
				del MASM.data[dictKey]
		return res

	@staticmethod
	def hasDataCheck(dictKey, expectedType = None):
		res = False
		with MASM.commLock:
			val = MASM.data.get(dictKey, None)
			if val is not None and (expectedType is None or type(val) is expectedType):
				res = True
		return res

def Start():
	MASM._startThread()

def OnQuit():
	MASM._stopAll()