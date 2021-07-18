import mido
import socketer

inPort = None
doReadInput = False

def Start():
	global inPort
	try:
		inPort = mido.open_input()
	except Exception as e:
		SE.Log(f"Could not open MIDI input: {e}")

def Update():
	global inPort
	global doReadInput
	if inPort is not None:
		if doReadInput and socketer.hasDataBool("MIDI_STOP"):
			doReadInput = False
		elif not doReadInput and socketer.hasDataBool("MIDI_START"):
			doReadInput = True
		for msg in inPort.iter_pending():
			if doReadInput: # We want to clear old pending messages but not send them if input is disabled
				binary = msg.bytes()
				if len(binary) >= 3:
					if  binary[0] == 144 and binary[2] > 0:
						socketer.sendData(f"MIDI_NOTE.{binary[1]}", binary[2])
					elif binary[0] == 128 or binary[2] == 0:
						socketer.sendData(f"MIDI_NOTE.{binary[1]}", 0)