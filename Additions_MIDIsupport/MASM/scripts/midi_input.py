import mido
import socketer

InPort = None
curMSG = None
curNote = None

def callbacker(message):
	global curMSG
	curMSG = message
	binary = curMSG.bin()
	if len(binary) > 1 and binary[1] > 0 and binary[2] > 0:
		curNote = binary[1]
		socketer.sendData("notedown.{}".format(curNote))
	elif len(binary) > 1 and binary[1] > 0 and binary[2] == 0:
		socketer.sendData("noteup.{}".format(binary[1]))
		curNote = 0
	else:
		curNote = 0

def Start():
	global InPort
	InPort = mido.open_input(callback=callbacker)