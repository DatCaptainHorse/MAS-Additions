import os
import facer
import pathlib
import socketer

detected = False
recognizing = False

dirPath = None
masmPath = None

preparedYet = False

# Prepares facial data
def facePrepare():
	global dirPath
	global masmPath
	global preparedYet
	
	# Whether we need to take images of face or not
	doTake = True

	# Setup some paths
	pDataPath = pathlib.Path(masmPath)/"face-data"
	pImagePath = pDataPath/"Player"
	pLBPHPath = pDataPath/"player.xml"
	
	# face-data path does not exist, create it
	if not pDataPath.exists():
		pDataPath.mkdir(parents = True, exist_ok = True)
	
	# existing facial data exists, load the data
	if pLBPHPath.exists():
		print("Loading facial data")
		facer.load_trained_lbph(pLBPHPath, ["Player"])
	else: # no existing data
		if pImagePath.exists(): # check if there are any existing images
			files = os.listdir(pImagePath)
			if len(files) == 0:
				doTake = True
			else:
				doTake = False
		else: # create path for images
			pImagePath.mkdir(parents = True, exist_ok = True)

		if doTake == True:
			print("No facial data found, please look at the camera while we take some")
			ret = facer.take_faces(pImagePath, 100, 0.01)
			if ret is False:
				return False
			
		res = facer.train_faces_lbph(pDataPath)
		if not res:
			return False

		facer.save_trained_lbph(pLBPHPath)
			
	preparedYet = True

	return True

times = 0
threshold = 0.6
alternater = False
def faceRecognize():
	global detected
	global preparedYet
	global alternater
	global threshold
	global times

	if not preparedYet:
		SE.Log("Error: Cannot recognize before preparing facial data")
		return False

	facer.camOn()

	if not detected:
		frame = facer.camFrame()

		# alternate between DNN and HAAR detection for recognizer, to be on safe side
		found, people = facer.recognize_faces_lbph(frame, threshold, alternater)
		if found:
			for person in people:
				if person[0] == None:
					times += 1
					print("Found someone x{} [{}]".format(times, person[2]), end='\r')
					# raise the threshold slowly each cycle just to recognize player eventually if the data is dirty
					if threshold < 0.9:
						threshold += 0.05
				else:
					print("\nFound {}".format(person[0]))
					detected = True
	else:
		facer.camOff()
		detected = False
		times = 0
		threshold = 0.6
		alternater = False
		return True

	alternater ^= 1

	return None
		

def Start():
	global dirPath
	global masmPath

	dirPath = os.path.dirname(os.path.realpath(__file__)) # Get our full path
	masmPath = os.path.dirname(dirPath) # get the our directory's parent directory (game folder)
	
def Update():
	global preparedYet
	global recognizing

	# Message received, start recognizing
	if socketer.hasData("recognizeFace"):
		print("Recognizing..")
		if preparedYet == False:
			err = facePrepare() # No data prepared this session, do so
			if err == False:
				SE.Log("Error when preparing data")
				socketer.sendData("cantSee") # failed to recognize
			else:
				recognizing = True
		else:
			recognizing = True

	# Non-blocking recognizion
	if recognizing:
		res = faceRecognize()
		if res != None:
			if res == True:
				socketer.sendData("seeYou") # recognized player
				recognizing = False
			elif res == False:
				SE.Log("Error, something went wrong during recognition")
				socketer.sendData("cantSee") # failed to recognize
				recognizing = False
