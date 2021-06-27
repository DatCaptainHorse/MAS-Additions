import os
import facer
import shutil
import pathlib
import socketer

useDNN = True
detected = False
recognizing = False
masmPath = None
preparedYet = False

# Prepares facial data
def facePrepare():
	global useDNN
	global masmPath
	global preparedYet

	# Whether we need to take images of face or not
	doTake = True
	# Setup some paths
	pDataPath = pathlib.Path(masmPath)/"face-data"
	pLBPHPath = pDataPath/"Player.xml"
	# face-data path does not exist, create it
	if not pDataPath.exists():
		pDataPath.mkdir(parents = True, exist_ok = True)
	# existing facial data exists, load the data
	if pLBPHPath.exists():
		print("Loading facial data")
		facer.load_trained_lbph(str(pLBPHPath), ["Player"])
		preparedYet = True
	else: # no existing data
		if doTake == True:
			print("No facial data found, please look at the camera while we take some")
			if facer.take_faces("Player", 100, 0.01) is False:
				return False

		if facer.train_faces_lbph() is False:
			return False

		facer.save_trained_lbph(str(pLBPHPath))
		# remove pictures from face-data folder as they aren't needed anymore
		#shutil.rmtree(pImagePath)
		preparedYet = True

	return True

times = 0
threshold = 0.6
def faceRecognize():
	global times
	global useDNN
	global detected
	global threshold
	global preparedYet

	if not preparedYet:
		SE.Log("Cannot recognize before preparing face data")
		return False

	facer.camOn()
	if not detected:
		frame = facer.camFrame()
		found, people = facer.recognize_faces_lbph(frame, threshold, useDNN)
		if found:
			for person in people:
				if not person[0]:
					times += 1
					print("Found someone x{} [{}]".format(times, person[2]), end="\r")
					# raise the threshold slowly each cycle just to recognize player eventually if the data is dirty
					if threshold < 0.9:
						threshold += 0.01
				else:
					print("\nFound {}".format(person[0]))
					detected = True
	else:
		facer.camOff()
		detected = False
		times = 0
		threshold = 0.6
		return True

	return None

def Start():
	global masmPath
	masmPath = os.path.dirname(os.path.realpath(__file__)) # Get our full path
	
def Update():
	global useDNN
	global preparedYet
	global recognizing
	# Message received, start recognizing
	res = socketer.hasDataWith("recognizeFace")
	if res:
		method = res.split(".")[1]
		if method == "HAAR":
			useDNN = False
		else:
			useDNN = True
		print(f"Recognizing with {method}")
		if preparedYet == False:
			if not facePrepare():
				SE.Log("Error when preparing data")
				socketer.sendData("cantSee") # failed to recognize
			else:
				recognizing = True
		else:
			recognizing = True

	# Non-blocking recognizion
	if recognizing:
		res = faceRecognize()
		if res:
			if res == True:
				socketer.sendData("seeYou") # recognized player
				recognizing = False
			elif res == False:
				SE.Log("Something went wrong during recognition")
				socketer.sendData("cantSee") # failed to recognize
				recognizing = False
				