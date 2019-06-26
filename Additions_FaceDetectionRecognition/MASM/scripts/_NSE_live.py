import sys, os
import cv2
import time

recog = False

start = time.time()
cap = cv2.VideoCapture(0)

dirPath = os.path.dirname(os.path.realpath(__file__))
realPath = os.path.dirname(dirPath)
faceCascade = cv2.CascadeClassifier(realPath + "/haarcascade_frontalface_alt.xml")

while(True):
	ret, frame = cap.read()
	if not ret:
		break

	gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
	gray = cv2.equalizeHist(gray)

	faces = faceCascade.detectMultiScale(
		gray,
		scaleFactor=1.2,
		minNeighbors=3,
		minSize=(20, 20)
	)

	if len(faces) >= 1:
		recog = True
		break
		
	# 8 seconds oughta be enough
	if (time.time() - start) > 8:
		recog = False
		break
		
cap.release()
if recog == True:
	print("YES")
else:
	print("NO")