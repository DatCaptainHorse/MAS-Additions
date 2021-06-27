# Just a script to make recognizing faces easier with few functions
# LBPH + HAAR recognizer combo is capable of identifying person from another, and training runtime
# DNN can be used in place for HAAR for detecting initial faces before LBPH recognition

import os
import time
import numpy as np
import cv2
import pathlib

face_recognizer_lbph = None
face_recognizer_dnn = None
persons = []
facelist = []
onCam = None

def camOn():
	global onCam
	if onCam == None:
		onCam = cv2.VideoCapture(0)

	if not onCam.isOpened():
		print("Unable to open camera")
		onCam = None
		return False

	return True

def camOff():
	global onCam
	if onCam == None:
		return True

	if onCam.isOpened():
		onCam.release()
		onCam = None
		return True

	return False

def camFrame():
	global onCam
	if not onCam.isOpened():
		print("Error: Camera no longer open")
		return False

	ret, frame = onCam.read()
	if not ret:
		return None
	else:
		return frame

	return False

# Takes pictures with the webcam and saves them to the output directory, used for training
def take_faces(personName, count, delay = 0.01, savePicturePath = None):
	global facelist
	global persons
	camOn()
	completed = 0
	while (completed < count):
		print ("Taking picture: {}/{}".format(completed + 1, count), end="\r")
		frame = camFrame()
		if frame is None:
			continue

		# Use DNN for taking faces always, way more accurate even if it takes longer
		faces = detect_faces_dnn(frame)
		if not faces:
			continue

		if len(faces) > 0:
			facelist.append(faces[0])
			if savePicturePath:
				try:
					cv2.imwrite(os.path.join(savePicturePath, "face_{}.png".format(completed)), faces[0])
				except:
					break
			completed += 1
		# Wait a bit
		time.sleep(delay)
	persons.append(personName)
	print("\n")
	camOff()
	return completed == count

# Detect any faces inside an image using haar cascades
# returns the face area images in gray and face rectangles
def detect_faces_haar(img, sceneGray = True):
	# Get the gray from image and equalize it
	gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
	gray = cv2.equalizeHist(gray)
	
	# Load haar face cascade
	realPath = os.path.dirname(os.path.realpath(__file__))
	face_cascade = cv2.CascadeClassifier(realPath + '/' + "haarcascade_frontalface_default.xml")

	# Detect faces with multiscale haar
	faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5)
	
	# No faces? Return nothing
	if (len(faces) == 0):
		return None

	grays = []
	
	for face in faces:
		(x, y, w, h) = face

		grayArea = None
		if sceneGray:
			grayArea = gray[y:y+w, x:x+h]
		else:
			area = img[y:y+w, x:x+h]
			grayArea = cv2.cvtColor(area, cv2.COLOR_BGR2GRAY)
			grayArea = cv2.equalizeHist(grayArea)
			
		grays.append(grayArea)
	
	return grays

# Detect any faces inside an image using deep neural networks
# uses pre-trained caffe models and protos
# returns the face area images in gray and face rectangles
def detect_faces_dnn(img, sceneGray = True):
	global face_recognizer_dnn
	realPath = os.path.dirname(os.path.realpath(__file__))
	# Load pre-trained model
	if face_recognizer_dnn is None:
		print ("Loading pre-trained model")
		face_recognizer_dnn = cv2.dnn.readNetFromCaffe(realPath + '/' + "MobileNet-SSD.prototxt", realPath + '/' + "MobileNet-SSD.caffemodel")

	# Resize image and blob it!
	(h, w) = img.shape[:2]
	resizedImg = cv2.resize(img, (224, 224))
	blobbed = cv2.dnn.blobFromImage(resizedImg, 1, (224, 224), (104, 117, 123))
	
	# Set the blobbed image as input for neural network, then forward it
	face_recognizer_dnn.setInput(blobbed)
	faces = face_recognizer_dnn.forward()
	
	# No faces? Return nothing
	if (len(faces) == 0):
		return None
	
	areas = []
	for i in range(0, faces.shape[2]):
		confidence = faces[0, 0, i, 2]
		
		if confidence < 0.2: # skip low confidence faces
			continue
		
		box = faces[0, 0, i, 3:7] * np.array([w, h, w, h])
		(sX, sY, eX, eY) = box.astype("int")
		
		grayed = None
		if sceneGray:
			grayed = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
			grayed = cv2.equalizeHist(grayed)
			grayed = grayed[sY:eY, sX:eX]
		else:
			cropped = img[sY:eY, sX:eX]
			grayed = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
			grayed = cv2.equalizeHist(grayed)
		areas.append(grayed)
	return areas
		
# Trains using taken data or images inside a folder, images must be in their own subfolder named after the person
# ex. images/MyName, and you give it "images" directory as the data_folder
def train_faces_lbph(data_folder = None):
	global face_recognizer_lbph
	global facelist
	labels = []
	if not face_recognizer_lbph:
		face_recognizer_lbph = cv2.face.LBPHFaceRecognizer_create()

	if data_folder:
		x = 0
		subdirs = os.listdir(data_folder)
		for subdir in subdirs:
			label = x
			persons.append(subdir)
			print("Preparing LBPH from images of {}".format(subdir))
			fileDir = os.path.join(data_folder, subdir)
			files = os.listdir(fileDir)
			pSize = len(files)
			for i, file in enumerate(files):
				# Prevent issues with files starting with a dot and non-image files
				if file.startswith(".") or not file.lower().endswith((".png", ".jpg", ".jpeg")):
					continue
				
				image_path = os.path.join(fileDir, file)
				image = cv2.imread(image_path)

				print("Progress: {}/{} images".format(i + 1, pSize), end="\r")

				if image:
					#image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) Already gray from HAAR
					labels.append(label)
					facelist.append(image)

			x = x + 1
			print('\n')
	else:
		print("Preparing LBPH from data")
		for f in facelist:
			labels.append(0)
		
	if len(facelist) <= 0 or len(labels) != len(facelist):
		print("Failed to prepare data")
		return False

	print("Training LBPH.. ", end="")
	try:
		face_recognizer_lbph.train(facelist, np.array(labels))
	except Exception as e:
		print("Failed, reason: {}".format(str(e)))
		return False

	print("Success")
	return True

# Save trained LBPH recognition algorithm
# requires that you train LBPH first
def save_trained_lbph(save_dir):
	global face_recognizer_lbph
	print("Saving LBPH.. ", end='')
	if not face_recognizer_lbph:
		print("Unable to save. LBPH recognizer not trained yet")
		return
	try:
		face_recognizer_lbph.write(save_dir)
	except Exception as e: 
		print("Unable to save. Reason: {}".format(e))
		return
		
	print("Success")
	
# Load trained LBPH recognition algorithm
# you need to give namelist with correct indices
def load_trained_lbph(load_dir, namelist):
	global face_recognizer_lbph
	global persons
	persons = namelist
	print("Loading LBPH.. ", end="")
	if not face_recognizer_lbph:
		face_recognizer_lbph = cv2.face.LBPHFaceRecognizer_create()
		
	face_recognizer_lbph.read(load_dir)
	print("Success")
	
# Attempts to recognize lbph trained faces within input image
# returns boolean if any face is detected and tuple of recognized faces
# tuple contains name and rectangle of face for each person (name is None if not recognized)
# argument threshold is the threshold for faces being recognized
# higher value is lower tolerance, meaning random faces 
# could be recognized as other people
def recognize_faces_lbph(image, threshold = 0.8, useDNN = False):
	global persons
	if image is not None:
		faces = None
		if useDNN:
			faces = detect_faces_dnn(image, True)
		else:
			faces = detect_faces_haar(image, True)
		
		recognized = []
		if faces:
			for face in faces:
				label, difference = face_recognizer_lbph.predict(face)
				if difference < (threshold * 100):
					name = persons[label]
					recognized.append(tuple((name, face, difference)))
				else:
					recognized.append(tuple((None, face, difference)))
			
		return True, recognized
	return False, None