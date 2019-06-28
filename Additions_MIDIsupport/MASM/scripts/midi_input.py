import mido
import socketer

InPort = None
curMSG = None

def Start():
	global InPort
	mido.set_backend('mido.backends.portmidi')
	InPort = mido.open_input()
	
def Render():
	global curMSG
	global InPort
	for msg in InPort.iter_pending():
		curMSG = msg
		binary = curMSG.bin()
		if len(binary) > 1 and binary[1] > 0:
			curNote = binary[1]
			if binary[0] == 144 and binary[2] > 0:
				socketer.sendData("notedown.{}".format(curNote))
			elif binary[2] == 0 or binary[0] == 128:
				socketer.sendData("noteup.{}".format(binary[1]))