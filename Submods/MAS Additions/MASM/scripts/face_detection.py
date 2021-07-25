import os
import time
import shutil
import pathlib
import socketer
import threading
from facer import Facer

masmPath = None
pDataPath = None
pLBPHPath = None
pNamePath = None

useDNN = False
failTimeout = 10
memoryTimeout = 3
lastAccess = False
preparedYet = False

detcThread = None
detcRun = threading.Event()
detcLock = threading.Lock()

# Prepares face-data
def facePrepare(retake = False, overrideTimeout = 0):
	global useDNN
	global masmPath
	global pDataPath
	global pLBPHPath
	global pNamePath
	global preparedYet
	global memoryTimeout
	# If recreation is desired, remove old data
	if retake is True:
		pLBPHPath.unlink(missing_ok = True)
		pNamePath.unlink(missing_ok = True)
	# face-data path does not exist, create it
	if not pDataPath.exists():
		pDataPath.mkdir(parents = True, exist_ok = True)
	# existing facial data exists, load the data
	if pLBPHPath.exists() and pNamePath.exists() and not preparedYet:
		print("Loading face-data")
		Facer.load_trained_lbph(str(pLBPHPath), str(pNamePath))
		preparedYet = True
	else: # no existing data or update
		if not retake and pLBPHPath.exists() and pNamePath.exists():
			print("Updating with new data..")
			if pLBPHPath.stat().st_size > 100000000 * (memoryTimeout / 5): # Limit max memory size
				print("Memory size limit reached, re-memorizing instead..")
				pLBPHPath.unlink(missing_ok = True)
				pNamePath.unlink(missing_ok = True)
				overrideTimeout = 0 # We want larger chunk of initial data, reset override
				retake = True
		else:
			print("No face-data found, taking..")
			socketer.sendData("FDAR_NOPREPAREDATA")
		try:
			chosenTimeout = memoryTimeout
			if overrideTimeout > 0:
				chosenTimeout = overrideTimeout
			if not Facer.take_faces("Player", count = 0, timeout = chosenTimeout, recreate = retake, minLightLevel = 15):
				return False
		except Facer.LightLevelLow:
			raise
		except Exception as e:
			SE.Log(f"Exception on taking data: {e}")
			return False

		try:
			if not Facer.train_faces_lbph(recreate = retake):
				socketer.sendData("FDAR_FAILURE")
				return False
		except Exception as e:
			SE.Log(f"Exception on train: {e}")
			socketer.sendData("FDAR_FAILURE")

		try:
			Facer.save_trained_lbph(str(pLBPHPath), str(pNamePath))
		except Exception as e:
			SE.Log(f"Exception on save: {e}")
			socketer.sendData("FDAR_FAILURE")

		preparedYet = True

	return True

# Data not prepared exception
class DataNotPrepared(Exception):
	pass

threshold = 0.60
# Recognizes all known people
# Returns list of recognized names
def recognizeKnown():
	global useDNN
	global detcLock
	global threshold
	global preparedYet
	if not preparedYet:
		SE.Log("Tried to recognize before data is prepared")
		raise DataNotPrepared
	else:
		try:
			Facer.camClearBuffer()
			frame = Facer.camFrame(minLightLevel = 15)
		except Facer.LightLevelLow:
			raise
		except Exception as e:
			SE.Log(f"Capture frame exception: {e}")
			socketer.sendData("FDAR_FAILURE")
			return None
		else:
			try:
				with detcLock:
					found, people = Facer.recognize_faces_lbph(frame, threshold, useDNN)
			except Exception as e:
				SE.Log(f"LBPH recognizing exception: {e}")
				#socketer.sendData("FDAR_FAILURE") # Disabled cuz hitting Python's nerve or something causing exception with random number, randomly. Works despite that
				return None
			else:
				if found:
					knownFound = []
					for person in people:
						if person[0] is None:
							#SE.Log("Found someone")
							#knownFound.append("FDAR_SOMEONE")
							# raise the threshold slowly to recognize person eventually
							if threshold < 0.8:
								threshold += 0.05
						else:
							SE.Log(f"Found {person[0]}")
							knownFound.append(person[0])
							if threshold > 0.6: # Keep threshold somewhere around where person can be detected
								threshold -= 0.06
					return knownFound
				else:
					SE.Log("Found nobody")
					return None
	socketer.sendData("FDAR_FAILURE")
	return None
	
# Non-blocking recognizion loop
def _recognizeLoop():
	global useDNN
	global detcRun
	global lastAccess
	global preparedYet
	global failTimeout
	if not preparedYet:
		SE.Log("Not prepared yet")
		try:
			if not facePrepare():
				SE.Log("Failed to prepare data")
				socketer.sendData("FDAR_FAILURE")
			else:
				socketer.sendData("FDAR_MEMORIZE_DONE")
		except Facer.LightLevelLow:
			SE.Log("Low-light on prepare")
			socketer.sendData("FDAR_MEMORIZE_LOWLIGHT")
		except Exception as e:
			SE.Log(f"Exception when preparing: {e}")
			socketer.sendData("FDAR_FAILURE")
			return
			
	lastTime = time.time()
	while not detcRun.is_set():
		toMemorize = socketer.hasDataValue("FDAR_MEMORIZE")
		if toMemorize is not None and lastAccess:
			try:
				(removeOld, override) = toMemorize
				if removeOld:
					preparedYet = False
				if not facePrepare(retake = removeOld, overrideTimeout = override):
					SE.Log("Failed to memorize")
					socketer.sendData("FDAR_FAILURE")
				else:
					socketer.sendData("FDAR_MEMORIZE_DONE")
			except Facer.LightLevelLow:
				SE.Log("Low-light on memorize")
				socketer.sendData("FDAR_MEMORIZE_LOWLIGHT")
			except Exception as e:
				SE.Log(f"Exception on memorize: {e}")
				socketer.sendData("FDAR_FAILURE")
		
		shouldRecognize = False
		toRecognize = socketer.hasDataValue("FDAR_RECOGNIZEONCE")
		if toRecognize is not None and lastAccess:
			if not preparedYet:
				SE.Log("Memory not prepared for recognition")
				socketer.sendData("FDAR_NOTMEMORIZED")
			else:
				shouldRecognize = True

		if shouldRecognize:
			startTime = time.time()
			while time.time() - startTime < failTimeout:
				if socketer.hasDataBool("FDAR_RECOGNIZESTOP"):
					shouldRecognize = False
					break
				elif time.time() - lastTime > 1.0: # Ease up on loop, attempt every second
					try:
						res = recognizeKnown()
					except Facer.LightLevelLow:
						SE.Log("Low-light on recognize")
						socketer.sendData("FDAR_LOWLIGHT") # No breaking here so we can fail eventually as we want to keep trying
					except DataNotPrepared:
						shouldRecognize = False
						break # We don't want to deal with this here.. Trust me I tried
					except Exception as e:
						SE.Log(f"Recognizing known exception: {e}")
						socketer.sendData("FDAR_FAILURE")
						shouldRecognize = False
						break
					else:
						if res is not None:
							for recognized in res:
								socketer.sendData("FDAR_RECOGNIZED", recognized)
							if toRecognize in res:
								shouldRecognize = False
								break
					lastTime = time.time()
				else:
					time.sleep(0.1)
		
		if socketer.hasDataBool("FDAR_RECOGNIZESTOP"):
			pass # Clear this so next recognitions won't fail immediately

		time.sleep(1) # No hogging CPU and data-locks!

def Update():
	global detcRun
	global detcLock
	global lastAccess
	global detcThread
	global preparedYet
	global failTimeout
	global memoryTimeout
	#socketer.hasData("FDAR_RECOGNIZENEW") # TODO: Recognize multiple people?
	newTimeout = socketer.hasDataValue("FDAR_SETTIMEOUT")
	if newTimeout and newTimeout > 0:
		failTimeout = newTimeout

	newMemoryTime = socketer.hasDataValue("FDAR_SETMEMORYTIMEOUT")
	if newMemoryTime and newMemoryTime > 0:
		memoryTimeout = newMemoryTime

	method = socketer.hasDataValue("FDAR_DETECTIONMETHOD")
	if method:
		if method == "HAAR":
			with detcLock:
				useDNN = False
		elif method == "DNN":
			with detcLock:
				useDNN = True

	# Message tells whether we are allowed to recognize or not
	allowAccess = socketer.hasDataValue("FDAR_ALLOWACCESS")
	if allowAccess is True and allowAccess != lastAccess:
		try:
			SE.Log("Recognition allowed")
			if not Facer.camOn():
				SE.Log("Camera failed to open")
			else:
				Facer.camFrame() # Turn on light with empty read
				detcRun.clear()
				if detcThread is None:
					detcThread = threading.Thread(target = _recognizeLoop)
				detcThread.start()
				lastAccess = allowAccess
		except Exception as e:
			SE.Log(f"Exception to start recognition thread: {e}")
			if not Facer.camOff(): # Just in case
				SE.Log("Camera failed to close?")
	elif allowAccess is False and allowAccess != lastAccess:
		try:
			SE.Log("Recognition not allowed")
			detcRun.set()
			if detcThread is not None:
				detcThread.join()
				detcThread = None
			if not Facer.camOff():
				SE.Log("Camera failed to close?")
			lastAccess = allowAccess
			preparedYet = False # So we can re-check for data existence
		except Exception as e:
			SE.Log(f"Exception to stop recognition thread: {e}")
			if not Facer.camOff(): # Just in case as well
				SE.Log("Camera failed to close?")

def Start():
	global masmPath
	global pDataPath
	global pLBPHPath
	global pNamePath
	global detcThread
	# Setup some paths
	masmPath = os.path.dirname(os.path.realpath(__file__)) # Get our full path
	pDataPath = pathlib.Path(masmPath)/"face-data" # Data folder
	pLBPHPath = pDataPath/"data-lbph.xml" # Data file
	pNamePath = pDataPath/"data-names.pkl" # Names file
	# Create thread
	detcThread = threading.Thread(target = _recognizeLoop)

def OnQuit():
	global detcRun
	global detcThread
	detcRun.set()
	detcThread.join()
	Facer.camOff()