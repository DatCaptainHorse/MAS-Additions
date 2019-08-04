# Just a script to make recognizing faces easier with few functions
# LBPH + HAAR recognizer combo is capable of identifying person from another, and training runtime
# DNN can be used in place for HAAR for detecting initial faces before LBPH recognition

import os
import time
import numpy as np
import cv2

face_recognizer_lbph = None
face_recognizer_dnn = None
persons = []
onCam = None

def camOn():
	global onCam
	if onCam == None:
		onCam = cv2.VideoCapture(0)

	if not onCam.isOpened():
		print("Unable to open camera")
		onCam == None
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
def take_faces(output_dir, count, delay = 0.1):
	global onCam

	camOn()
	
	completed = 0
	while (completed < count):
		print ("Taking picture: {}/{}".format(completed + 1, count), end="\r")
		frame = camFrame()
		if frame is None:
			continue
			
		faces = detect_faces_dnn(frame)
		if faces == None:
			continue

		if len(faces) > 0:
			img_name = output_dir + '/' + "face_{}.png".format(completed)
			try:
				cv2.imwrite(img_name, faces[0])
			except:
				break

			completed = completed + 1

		# Wait a bit
		time.sleep(delay)

	camOff()

	if completed == count:
		return True
	else:
		return False

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
		print ("Loading pre-trained Caffe model")
		face_recognizer_dnn = cv2.dnn.readNetFromCaffe(realPath + '/' + "face.prototxt", realPath + '/' + "face.caffemodel")

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
		
# Trains using any images inside a folder, images must be in their own subfolder, subfolders named after the persons
# ex. images/MyName, and you give it "images" directory as the data_folder
def train_faces_lbph(data_folder):
	global face_recognizer_lbph
	labels = []
	facelist = []
	
	if face_recognizer_lbph is None:
		face_recognizer_lbph = cv2.face.LBPHFaceRecognizer_create()
		
	subdirs = os.listdir(data_folder)
	
	x = 0
	for subdir in subdirs:
		label = x
		persons.append(subdir)
		
		print("Preparing LBPH of {}".format(subdir))
		
		fileDir = os.path.join(data_folder, subdir)
		files = os.listdir(fileDir)
		pSize = len(files)
		
		for i, file in enumerate(files):
			# Prevent issues with files starting with a dot
			# and non-image files
			if (file.startswith(".")
			or not file.lower().endswith(('.png', '.jpg', '.jpeg'))):
				continue
			
			image_path = os.path.join(fileDir, file)
			image = cv2.imread(image_path)
			
			print("Progress: {}/{} images".format(i + 1, pSize), end='\r')

			if image is not None:
				image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
				labels.append(label)
				facelist.append(image)

		x = x + 1
		
		print('\n')
		
	if len(facelist) <= 0:
		print("Failed to prepare data")
		return False

	print("Training LBPH.. ", end='')
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
	
	if face_recognizer_lbph is None:
		print("Unable to save. LBPH recognizer not trained yet")
		return
	
	face_recognizer_lbph.write(save_dir)
	
# Load trained LBPH recognition algorithm
# you need to give namelist with correct indices
def load_trained_lbph(load_dir, namelist):
	global face_recognizer_lbph
	global persons
	
	persons = namelist
	
	if face_recognizer_lbph is None:
		face_recognizer_lbph = cv2.face.LBPHFaceRecognizer_create()
		
	face_recognizer_lbph.read(load_dir)
	
# Attempts to recognize lbph trained faces within input image
# returns boolean if any face is detected and tuple of recognized faces
# tuple contains name and rectangle of face for each person (name is None if not recognized)
# argument threshold is the threshold for faces being recognized
# higher value is lower tolerance, meaning random faces 
# could be recognized as other people
def recognize_faces_lbph(imgin, threshold = 0.8, useDNN = False):
	image = None

	if imgin is not None:
		if isinstance(imgin, str):
			image = cv2.imread(imgin)
		else:
			image = imgin.copy()

		if image is None:
			return False, None
			
		faces = None
		if useDNN:
			faces = detect_faces_dnn(image, True)
		else:
			faces = detect_faces_haar(image, True)
		
		recognized = []
		if faces is not None:
			for i, face in enumerate(faces):
				label, difference = face_recognizer_lbph.predict(face)
				#cv2.imshow("IMG", face)
				#cv2.waitKey(0)
				#print("{}, {}".format(label, difference))
				if difference < (threshold * 100):
					name = persons[label]
					recognized.append(tuple((name, faces[i], difference)))
				else:
					recognized.append(tuple((None, faces[i], difference)))
			
		return True, recognized
	return False, None