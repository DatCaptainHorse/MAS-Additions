# Just a script to make recognizing faces easier with few functions
# LBPH + HAAR recognizer combo is capable of identifying person from another, and training runtime
# DNN can be used in place for HAAR for detecting initial faces before LBPH recognition

import os
import time
import numpy as np
import cv2
import pathlib
import pickle

face_recognizer_lbph = None
face_recognizer_dnn = None
people = {}
nameIndex = {}
onCam = None

realPath = os.path.dirname(os.path.realpath(__file__))
face_cascade = cv2.CascadeClassifier(realPath + '/' + "haarcascade_frontalface_default.xml")

# Convert image to HSV and increase V (brightness) by value
# Returns image with increased brightness
def increase_brightness(image, value):
	if value > 0:
		hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
		h, s, v = cv2.split(hsv)
		limit = 255 - value
		v[v > limit] = 255
		v[v <= limit] += value
		hsv = cv2.merge((h, s, v))
		image = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
	return image

def camOn():
	global onCam
	if onCam is None:
		onCam = cv2.VideoCapture(0)

	if not onCam.isOpened():
		print("Unable to open camera")
		onCam = None
		return False

	return True

def camOff():
	global onCam
	if onCam is None:
		return True

	if onCam.isOpened():
		onCam.release()
		onCam = None
		return True

	return False

class LightLevelLow(Exception):
	pass

# Returns frame on success, None if camera cannot be opened or None if reading frame failed
# Parameter minLightLevel specifies the minimum brightness allowed, if brightness is too low LightLevelLow is thrown
def camFrame(minLightLevel = 0):
	global onCam
	if not onCam or not onCam.isOpened():
		print("Error: Camera not open")
		return None

	ret, frame = onCam.read()
	if not ret or frame is None:
		return None

	if minLightLevel > 0:
		if np.mean(frame) < minLightLevel:
			raise LightLevelLow

	return frame

# Takes pictures with webcam, used for training, if count is 0 timeout is used as main count
# If minLightLevel is greater than 0 and it's not hit, LightLevelLow is thrown
def take_faces(personName, count = 100, timeout = 3, savePicturePath = None, recreate = False, useDNN = False, minLightLevel = 0):
	global people
	global nameIndex
	completed = 0
	if recreate:
		people = {}
		nameIndex = {}

	facelist = []
	startTime = time.time()
	while time.time() - startTime < timeout:
		dt = time.time()
		if count > 0 and completed >= count:
			break

		if count > 0:
			print (f"Taking frame: {completed + 1}/{count}", end="\r")
		else:
			print (f"Taking frame: {completed + 1}", end="\r")

		try:
			frame = camFrame(minLightLevel)
		except LightLevelLow:
			raise

		if frame is None:
			timeout += time.time() - dt
			continue

		# Use DNN for taking faces always, way more accurate even if it takes longer
		faces = None
		if useDNN:
			faces = detect_faces_dnn(frame)
		else:
			faces = detect_faces_haar(frame)

		if faces is None or len(faces) == 0:
			timeout += time.time() - dt
			continue

		facelist.append(faces[0]) # Append first found face
		if savePicturePath:
			try:
				cv2.imwrite(os.path.join(savePicturePath, f"{personName}/face_{completed}.png"), faces[0])
			except Exception as e:
				print(f"Failed to save frame: {e}")
				return False
				
		completed += 1

	print("\n")
	if len(facelist) > 0:
		idx = nameIndex.get(personName, len(people))
		people[idx] = facelist
		nameIndex[personName] = idx
	else:
		print("List empty after take")
		return False

	if count > 0:
		return completed == count
	else:
		return True

# Detect any faces inside an image using haar cascades
# returns the face area images in gray and face rectangles
def detect_faces_haar(img, sceneGray = True):
	global realPath
	global face_cascade
	# Get the gray from image and equalize it
	gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
	gray = cv2.equalizeHist(gray)
	
	# Detect faces with multiscale haar
	faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
	
	# No faces? Return nothing
	if len(faces) == 0:
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
		
		if grayArea is not None:
			grays.append(grayArea)
	
	return grays

# Detect any faces inside an image using deep neural networks
# uses pre-trained caffe models and protos
# returns the face area images in gray and face rectangles
def detect_faces_dnn(img, sceneGray = True):
	global realPath
	global face_recognizer_dnn
	# Load pre-trained model
	if face_recognizer_dnn is None:
		print ("Loading caffe model")
		face_recognizer_dnn = cv2.dnn.readNetFromCaffe(realPath + '/' + "MobileNet-SSD.prototxt", realPath + '/' + "MobileNet-SSD.caffemodel")

	# Resize image and blob it
	(h, w) = img.shape[:2]
	resizedImg = cv2.resize(img, (224, 224))
	blobbed = cv2.dnn.blobFromImage(resizedImg, 1, (224, 224), (104, 117, 123))
	
	# Set the blobbed image as input for neural network, then forward it
	face_recognizer_dnn.setInput(blobbed)
	faces = face_recognizer_dnn.forward()
	
	# No faces? Return nothing
	if len(faces) == 0:
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

		if grayed is not None:
			areas.append(grayed)
		
	return areas
		
# Trains using taken data or images inside a folder, images must be in their own subfolder named after the person
# ex. images/MyName, and you give it "images" directory as the data_folder
def train_faces_lbph(data_folder = None, recreate = False):
	global people
	global nameIndex
	global face_recognizer_lbph
	requireOneTime = False
	if face_recognizer_lbph is None or recreate is True:
		requireOneTime = True
		face_recognizer_lbph = cv2.face.LBPHFaceRecognizer_create()
		
	if data_folder:
		subdirs = os.listdir(data_folder)
		for subdir in subdirs:
			print("Preparing LBPH from images of {}".format(subdir))
			fileDir = os.path.join(data_folder, subdir)
			files = os.listdir(fileDir)
			pSize = len(files)
			facelist = []
			for i, file in enumerate(files):
				# Prevent issues with files starting with a dot and non-image files
				if file.startswith(".") or not file.lower().endswith((".png", ".jpg", ".jpeg")):
					continue
				
				image_path = os.path.join(fileDir, file)
				image = cv2.imread(image_path)

				print(f"Progress: {i+1}/{pSize} images", end="\r")
				if image is not None:
					facelist.append(image)

			if len(facelist) > 0:
				idx = nameIndex.get(subdir, len(people))
				people[idx] = facelist
				nameIndex[subdir] = idx
			else:
				print("Error: facelist empty loading from folder")

			print('\n')
	else:
		print("Preparing LBPH from data")
		
	if len(people) == 0:
		print("Failed to prepare data")
		return False

	print("Training LBPH.. ", end="")
	try:
		for index, data in people.items():
			labels = []
			datalist = []
			for d in data:
				labels.append(index)
				datalist.append(d)

			if len(labels) > 0 and len(datalist) > 0:
				if requireOneTime is True:
					requireOneTime = False
					face_recognizer_lbph.train(datalist, np.array(labels))
					print("Trained")
				else:
					face_recognizer_lbph.update(datalist, np.array(labels))
					print("Updated")
			else:
				print("Error: Empty or mismatched data")
	except Exception as e:
		print(f"Failed, reason: {e}")
		return False

	return True

# Save trained LBPH recognition data
# requires that you train LBPH first
def save_trained_lbph(lbph_path, names_path):
	global nameIndex
	global face_recognizer_lbph
	print("Saving LBPH.. ", end="")
	if not face_recognizer_lbph:
		print("Unable to save. LBPH recognizer not trained yet")
		return
	try:
		face_recognizer_lbph.write(lbph_path)
		with open(names_path, "wb") as f:
			pickle.dump(nameIndex, f)
		print("Success")
	except Exception as e: 
		print(f"Unable to save. Reason: {e}")
	
# Load trained LBPH recognition data
def load_trained_lbph(lbph_path, names_path):
	global nameIndex
	global face_recognizer_lbph
	print("Loading LBPH.. ", end="")
	if not face_recognizer_lbph:
		face_recognizer_lbph = cv2.face.LBPHFaceRecognizer_create()
	try:
		face_recognizer_lbph.read(lbph_path)
		with open(names_path, "rb") as f:
			nameIndex = pickle.load(f)
		print(f"Success, indexes: {nameIndex}")
	except Exception as e:
		print(f"Exception on load: {e}")
	
# Attempts to recognize lbph trained faces within input image
# returns boolean if any face is detected and tuple of recognized faces
# tuple contains index and rectangle of face for each person (name is None if not recognized)
# argument threshold is the threshold for faces being recognized
# higher value is lower tolerance, meaning random faces 
# could be recognized as other people
def recognize_faces_lbph(image, threshold = 0.8, useDNN = False):
	global nameIndex
	if image is not None:
		try:
			if useDNN:
				faces = detect_faces_dnn(image)
			else:
				faces = detect_faces_haar(image)
		except Exception as e:
			print(f"Detection error: {e}")
			return False, None
		else:
			if faces is not None:
				found = False
				recognized = []
				for face in faces:
					try:
						label, difference = face_recognizer_lbph.predict(face)
					except Exception as e:
						print(f"Could not predict: {e}")
						return False, None
					else:
						try:
							found = True
							if difference < (threshold * 100):
								name = None
								for k, v in nameIndex.items():
									if v == label:
										name = k
										break
								recognized.append((name, face))
							else:
								recognized.append((None, face))
						except Exception as e:
							print(f"Exception on recognized append: {e}")
							return False, None
				return found, recognized
			return False, None
		return False, None
	return False, None