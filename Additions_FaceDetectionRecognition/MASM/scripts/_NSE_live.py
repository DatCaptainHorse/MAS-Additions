import sys, os
import cv2
import time

recog = False

start = time.time()
cap = cv2.VideoCapture(0)

dirPath = os.path.dirname(os.path.realpath(__file__))
realPath = os.path.dirname(dirPath)
faceCascade = cv2.CascadeClassifier(realPath + "/haarcascade_frontalface_default.xml")

while(True):
	ret, frame = cap.read()
	gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

	faces = faceCascade.detectMultiScale(
		gray,
		scaleFactor=1.1,
		minNeighbors=5,
		minSize=(30, 30)
	)

	# Draw a rectangle around the faces
	if len(faces) >= 1:
		recog = True
		break
		
	if (time.time() - start) > 5:
		recog = False
		break
		
cap.release()
if recog == True:
	print("YES")
else:
	print("NO")