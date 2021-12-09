import mido
from socketer import MASM

inPort = None
doReadInput = False

def Start():
	global inPort
	try:
		print(f"MIDI inputs: {mido.get_input_names()}")
		inPort = mido.open_input()
		print(f"MIDI input open: {inPort}")
	except Exception as e:
		inPort = None
		print(f"Could not open MIDI input: {e}")

def Update():
	global inPort
	global doReadInput
	if inPort is not None:
		if doReadInput and MASM.hasDataBool("MIDI_STOP"):
			doReadInput = False
		elif not doReadInput and MASM.hasDataBool("MIDI_START"):
			doReadInput = True
		for msg in inPort.iter_pending():
			if MASM.hasDataCheck("MIDI_KEYMAPKEY"):
				bytes = msg.bytes()
				if len(bytes) >= 3:
					MASM.hasDataBool("MIDI_KEYMAPKEY")
					MASM.sendData("MIDI_KEY", bytes[1])
			elif doReadInput: # We want to clear old pending messages but not send them if input is disabled
				bytes = msg.bytes()
				if len(bytes) >= 3:
					if bytes[0] == 144 and bytes[2] > 0:
						MASM.sendData(f"MIDI_NOTE.{bytes[1]}", bytes[2])
					elif bytes[0] == 128 or bytes[2] == 0:
						MASM.sendData(f"MIDI_NOTE.{bytes[1]}", 0)