import mido
import socketer

InPort = None

def Start():
	global InPort
	try:
		InPort = mido.open_input()
	except:
		pass # No MIDI device found, just pass

def Update():
	global InPort
	if InPort is not None:
		for msg in InPort.iter_pending():
			binary = msg.bytes()
			if len(binary) >= 3:
				if binary[0] == 144 and binary[2] > 0:
					socketer.sendData(f"notedown.{binary[1]}.{binary[2]}")
				elif binary[0] == 128 or binary[2] == 0:
					socketer.sendData(f"noteup.{binary[1]}.0")