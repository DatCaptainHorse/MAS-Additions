import os
import time
import shutil
import pathlib
from socketer import MASM
import threading
from facer import Facer

masmPath = None
pDataPath = None
pLBPHPath = None
pNamePath = None

detcMethod = 0 # 0 HAAR, 1 DNN, 2 BOTH
failTimeout = 10
memoryTimeout = 5
lastAccess = False
preparedYet = False
keepWebcamOpen = None
chosenCam = 0

detcThread = None
detcRun = threading.Event()
detcLock = threading.Lock()

# Prepares face-data
def facePrepare(retake = False, overrideTimeout = 0):
	global masmPath
	global pDataPath
	global pLBPHPath
	global pNamePath
	global detcMethod
	global preparedYet
	global memoryTimeout
	global keepWebcamOpen
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
			MASM.sendData("FDAR_NOPREPAREDATA")

		chosenTimeout = memoryTimeout
		if overrideTimeout > 0:
			chosenTimeout = overrideTimeout
		try:
			if not keepWebcamOpen and not Facer.camOn():
				print("Camera failed to open")
				if not Facer.camOff():
					print("Camera failed to close?")
				return False
			takeDNN = False
			if detcMethod == 1 or detcMethod == 2:
				takeDNN = True
			if not Facer.take_faces("Player", count = 0, timeout = chosenTimeout, recreate = retake, useDNN = takeDNN, minLightLevel = 15):
				if not keepWebcamOpen and not Facer.camOff():
					print("Camera failed to close?")
				return False
			if not keepWebcamOpen and not Facer.camOff():
				print("Camera failed to close?")
		except Facer.LightLevelLow:
			if not keepWebcamOpen and not Facer.camOff():
				print("Camera failed to close?")
			raise
		except Facer.NoFacesFound:
			print(f"Face couldn't be found within {chosenTimeout*2}s")
			if not keepWebcamOpen and not Facer.camOff():
				print("Camera failed to close?")
			return False
		except Exception as e:
			print(f"Exception on taking data: {e}")
			if not keepWebcamOpen and not Facer.camOff():
				print("Camera failed to close?")
			return False

		try:
			if not Facer.train_faces_lbph(recreate = retake):
				MASM.sendData("FDAR_FAILURE")
				return False
		except Exception as e:
			print(f"Exception on train: {e}")
			MASM.sendData("FDAR_FAILURE")

		try:
			Facer.save_trained_lbph(str(pLBPHPath), str(pNamePath))
		except Exception as e:
			print(f"Exception on save: {e}")
			MASM.sendData("FDAR_FAILURE")

		preparedYet = True

	return True

# Data not prepared exception
class DataNotPrepared(Exception):
	pass

threshold = 0.6
methodSwitch = False
# Recognizes all known people
# Returns list of recognized names
def recognizeKnown():
	global threshold
	global detcMethod
	global preparedYet
	global methodSwitch
	if not preparedYet:
		print("Tried to recognize before data is prepared")
		raise DataNotPrepared
	else:
		try:
			Facer.camClearBuffer()
			frame = Facer.camFrame(minLightLevel = 15)
		except Facer.LightLevelLow:
			raise
		except Exception as e:
			print(f"Capture frame exception: {e}")
			MASM.sendData("FDAR_FAILURE")
			return None
		else:
			try:
				if detcMethod == 0:
					methodSwitch = False
				elif detcMethod == 1:
					methodSwitch = True
				elif detcMethod == 2:
					methodSwitch = not methodSwitch
				found, people = Facer.recognize_faces_lbph(frame, threshold, methodSwitch)
			except Exception as e:
				print(f"LBPH recognizing exception: {e}")
				#MASM.sendData("FDAR_FAILURE") # Disabled cuz hitting Python's nerve or something causing exception with random number, randomly. Works despite that
				return None
			else:
				if found:
					knownFound = []
					for person in people:
						if person[0] is None:
							#print("Found someone")
							#knownFound.append("FDAR_SOMEONE")
							# raise the threshold slowly to recognize person eventually
							if threshold < 0.8:
								threshold += 0.05
						else:
							print(f"Found {person[0]}")
							knownFound.append(person[0])
							if threshold > 0.6: # Keep threshold somewhere around where person can be detected
								threshold -= 0.06
					return knownFound
				else:
					print("Found nobody")
					return None
	MASM.sendData("FDAR_FAILURE")
	return None
	
# Non-blocking recognizion loop
def _recognizeLoop():
	global detcRun
	global lastAccess
	global preparedYet
	global failTimeout
	global keepWebcamOpen
	if not preparedYet:
		print("Not prepared yet")
		try:
			if not facePrepare():
				print("Failed to prepare data")
				MASM.sendData("FDAR_FAILURE")
			else:
				MASM.sendData("FDAR_MEMORIZE_DONE")
		except Facer.LightLevelLow:
			print("Low-light on prepare")
			MASM.sendData("FDAR_MEMORIZE_LOWLIGHT")
		except Exception as e:
			print(f"Exception when preparing: {e}")
			MASM.sendData("FDAR_FAILURE")
			return
			
	lastTime = time.time()
	while not detcRun.is_set():
		toMemorize = MASM.hasDataValue("FDAR_MEMORIZE")
		if toMemorize is not None and lastAccess:
			try:
				(removeOld, override) = toMemorize
				if removeOld:
					preparedYet = False
				if not facePrepare(retake = removeOld, overrideTimeout = override):
					print("Failed to memorize")
					MASM.sendData("FDAR_FAILURE")
				else:
					MASM.sendData("FDAR_MEMORIZE_DONE")
			except Facer.LightLevelLow:
				print("Low-light on memorize")
				MASM.sendData("FDAR_MEMORIZE_LOWLIGHT")
			except Exception as e:
				print(f"Exception on memorize: {e}")
				MASM.sendData("FDAR_FAILURE")
		
		shouldRecognize = False
		toRecognize = MASM.hasDataValue("FDAR_RECOGNIZEONCE")
		if toRecognize is not None and lastAccess:
			if not preparedYet:
				print("Memory not prepared for recognition")
				MASM.sendData("FDAR_NOTMEMORIZED")
			else:
				shouldRecognize = True

		if shouldRecognize:
			if not keepWebcamOpen and not Facer.camOn():
				print("Camera failed to open")
				MASM.sendData("FDAR_FAILURE")
				shouldRecognize = False
			else:
				startTime = time.time()
				while time.time() - startTime < failTimeout:
					if MASM.hasDataBool("FDAR_RECOGNIZESTOP"):
						shouldRecognize = False
						break
					elif time.time() - lastTime > 1.0: # Ease up on loop, attempt every second
						try:
							res = recognizeKnown()
						except Facer.LightLevelLow:
							print("Low-light on recognize")
							MASM.sendData("FDAR_LOWLIGHT") # No breaking here so we can fail eventually as we want to keep trying
						except DataNotPrepared:
							shouldRecognize = False
							break # We don't want to deal with this here.. Trust me I tried
						except Exception as e:
							print(f"Recognizing known exception: {e}")
							MASM.sendData("FDAR_FAILURE")
							shouldRecognize = False
							break
						else:
							if res is not None:
								for recognized in res:
									MASM.sendData("FDAR_RECOGNIZED", recognized)
								if toRecognize in res:
									shouldRecognize = False
									break
						lastTime = time.time()
					else:
						time.sleep(0.1)

				if not keepWebcamOpen and not Facer.camOff():
					print("Camera failed to close?")

				if MASM.hasDataBool("FDAR_RECOGNIZESTOP"):
					pass # Clear this so next recognitions won't fail immediately if duplicate data is received

		time.sleep(1) # No hogging CPU and data-locks!

def Update():
	global detcRun
	global chosenCam
	global detcMethod
	global lastAccess
	global detcThread
	global preparedYet
	global failTimeout
	global memoryTimeout
	global keepWebcamOpen

	# TODO: Recognize multiple people?
	if MASM.hasDataCheck("FDAR_KEEPOPEN", bool):
		newKeepOpen = MASM.hasDataValue("FDAR_KEEPOPEN")
		if lastAccess:
			if keepWebcamOpen and not newKeepOpen and not Facer.camOff():
				print("Camera failed to close?")
			elif not keepWebcamOpen and newKeepOpen:
				if not Facer.camOn():
					print("Camera failed to open")
					MASM.sendData("FDAR_FAILURE")
				else:
					Facer.camFrame() # Turn on light
					MASM.sendData("FDAR_CAMON")
		keepWebcamOpen = newKeepOpen

	if MASM.hasDataCheck("FDAR_SETTIMEOUT", int):
		if (newVal := MASM.hasDataValue("FDAR_SETTIMEOUT", 0)) > 0:
			failTimeout = newVal

	if MASM.hasDataCheck("FDAR_SETMEMORYTIMEOUT", int):
		if (newVal := MASM.hasDataValue("FDAR_SETMEMORYTIMEOUT", 0)) > 0:
			memoryTimeout = newVal

	method = MASM.hasDataValue("FDAR_DETECTIONMETHOD")
	if method is not None:
		if method == "HAAR":
			detcMethod = 0
		elif method == "DNN":
			detcMethod = 1
		elif method == "BOTH":
			detcMethod = 2

	if MASM.hasDataBool("FDAR_GETCAMS"):
		if keepWebcamOpen:
			Facer.camOff()
		MASM.sendData("FDAR_CAMSLIST", Facer.getCams())
		if keepWebcamOpen:
			Facer.camOn()
			Facer.camFrame()

	if MASM.hasDataCheck("FDAR_SETCAM", int):
		chosenCam = MASM.hasDataValue("FDAR_SETCAM", 0)

	if MASM.hasDataBool("FDAR_TESTCAM"):
		try:
			if keepWebcamOpen:
				Facer.camOff()
				Facer.camOn(id = chosenCam)
				Facer.camFrame()
			else:
				Facer.camOn(id = chosenCam)
				Facer.camFrame()
				time.sleep(3) # Yes, bad
				Facer.camOff()
		except Exception as e:
			print(f"Error wat: {e}")

	# Message tells whether we are allowed to recognize or not
	allowAccess = MASM.hasDataValue("FDAR_ALLOWACCESS")
	if allowAccess is True and allowAccess != lastAccess:
		try:
			print("Recognition allowed")
			if keepWebcamOpen and not Facer.camOn():
				print("Camera failed to open")
			else:
				if keepWebcamOpen:
					Facer.camFrame() # Turn on light with empty read
				detcRun.clear()
				if detcThread is None:
					detcThread = threading.Thread(target = _recognizeLoop)
				detcThread.start()
				lastAccess = allowAccess
		except Exception as e:
			print(f"Exception to start recognition thread: {e}")
			if not Facer.camOff(): # Just in case
				print("Camera failed to close?")
	elif allowAccess is False and allowAccess != lastAccess:
		try:
			print("Recognition not allowed")
			detcRun.set()
			if detcThread is not None:
				detcThread.join()
				detcThread = None
			if not Facer.camOff():
				print("Camera failed to close?")
			lastAccess = allowAccess
			preparedYet = False # So we can re-check for data existence
		except Exception as e:
			print(f"Exception to stop recognition thread: {e}")
			if not Facer.camOff(): # Just in case as well
				print("Camera failed to close?")

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