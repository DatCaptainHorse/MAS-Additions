# Temporary quick & cheaty implementation before Python 3.8 is released
# along with official modules like numpy and cv2 for Python 3.8

import os
import subprocess
import socket
import socketer

def faceRecognize():
	dirPath = os.path.dirname(os.path.realpath(__file__))
	masmPath = os.path.dirname(dirPath)
	res = subprocess.check_output(["python", masmPath + "/scripts/_NSE_live.py"], shell=True).decode('utf-8')
	print("Received {}".format(res))
	if "YES" in res:
		return True
	else:
		return False

def Update():
	# Message received, start recognizing
	if socketer.hasData("recognizeFace"):
		print("Recognizing..")
		res = faceRecognize()
		if res != None:
			if res == True:
				socketer.sendData("seeYou") # recognized player
			else:
				socketer.sendData("cantSee") # failed to recognize

'''
import os
import socket
import cv2
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
	pDataPath = masmPath + '\\' + "face-data"
	pImagePath = pDataPath + '\\' + "Player"
	pLBPHPath = os.path.relpath(pDataPath + '\\' + "player.xml")
	
	# face-data path does not exist, create it
	if not pathlib.Path(pDataPath).exists():
		pathlib.Path(pDataPath).mkdir(parents = True, exist_ok = True)
	
	# existing facial data exists, load the data
	if pathlib.Path(pLBPHPath).exists():
		print("Loading facial data")
		facer.load_trained_lbph(pLBPHPath, ["Player"])
	else: # no existing data
		if pathlib.Path(pImagePath).exists(): # check if there are any existing images
			files = os.listdir(pImagePath)
			if len(files) < 1:
				doTake = True
			else:
				doTake = False
		else: # create path for images
			pathlib.Path(pImagePath).mkdir(parents = True, exist_ok = True)

		if doTake == True:
			print("No facial data found, please look at the camera while we take some")
			ret = facer.take_faces(pImagePath, 25, 0.1)
			if ret is False:
				return False
			
		facer.train_faces_lbph(pDataPath)
		facer.save_trained_lbph(pLBPHPath)
			
	preparedYet = True

	return True


times = 0	
def faceRecognize():
	global detected
	global preparedYet
	global times

	if not preparedYet:
		SE.Log("Error: Cannot recognize before preparing facial data")
		return False

	facer.camOn()

	if not detected:
		frame = facer.camFrame()

		found, people = facer.recognize_faces_lbph(frame, 0.6)
		if found:
			for person in people:
				if person[0] == None:
					times += 1
					print("Found someone x{}".format(times), end='\r')
				else:
					print("\nFound {}".format(person[0]))
					detected = True
	else:
		facer.camOff()
		detected = False
		times = 0
		return True

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
			recognizing = facePrepare() # No data prepared this session, do so
			if recognizing == False:
				SE.Log("Error when preparing data")

	# Non-blocking recognizion
	if recognizing:
		res = faceRecognize()
		if res != None:
			if res == True:
				socketer.sendData("seeYou") # recognized player
				recognizing = False
			elif res == False:
				socketer.sendData("cantSee") # failed to recognize
				recognizing = False
'''