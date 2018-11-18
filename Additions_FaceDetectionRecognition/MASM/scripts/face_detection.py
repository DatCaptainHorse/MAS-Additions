import os
import socket
import numpy.core.multiarray
import cv2
import facer
import pathlib
import socketer

detected = False
errored = False

dirPath = None
masmPath = None

preparedYet = False

cam = None

def facePrepare():
	global detected
	global errored
	global dirPath
	global masmPath
	global cam
	global preparedYet
	
	doTake = True
	pDataPath = masmPath + '\\' + "face-data"
	pImagePath = pDataPath + '\\' + "Player"
	pLBPHPath = os.path.relpath(pDataPath + '\\' + "player.xml")
	
	if not pathlib.Path(pDataPath).exists():
		pathlib.Path(pDataPath).mkdir(parents = True, exist_ok = True)
	
	if pathlib.Path(pLBPHPath).exists():
		print("Loading facial data")
		facer.load_trained_lbph(pLBPHPath, ["Player"])
	else:
		if pathlib.Path(pImagePath).exists():
			files = os.listdir(pImagePath)
			if len(files) < 1:
				doTake = True
			else:
				doTake = False
				
		pathlib.Path(pImagePath).mkdir(parents = True, exist_ok = True)
		if doTake:
			SE.Log("No facial data found, please look at the camera while we take some")
			facer.take_faces(pImagePath, 25, 0.1)
			
		facer.train_faces_lbph(pDataPath)
		facer.save_trained_lbph(pLBPHPath)
			
	cam = cv2.VideoCapture(0)
	preparedYet = True

	
def faceRecognize():
	global detected
	global errored
	global cam
	
	# Will block stuff, oh well.
	while True:
		if not detected and not errored:
			if not cam.isOpened():
				SE.Log("Error: Unable to open camera")
				socketer.sendData("cantSee")
				errored = True
				break
	
			ret, frame = cam.read()
		
			if ret is True:
				if frame is not None:
					found, people = facer.recognize_faces_lbph(frame, 0.6)
					if found:
						for person in people:
							if person[0] is None:
								SE.Log("Found someone")
							else:
								SE.Log("Found {}".format(person[0]))
								socketer.sendData("seeYou")
								detected = True
								cam.release()
								break
			
		else:
			cam.release()
			break

def Start():
	global dirPath
	global masmPath

	dirPath = os.path.dirname(os.path.realpath(__file__)) # Get our full path
	masmPath = os.path.dirname(dirPath) # get the our directory's parent directory (game folder)
	
def Update():
	global preparedYet
	global alreadyRecognizing
	
	if socketer.data == 'recognizeFace':
		if not preparedYet:
			facePrepare()
			
		faceRecognize()