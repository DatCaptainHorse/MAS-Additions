import rtmidi2
from socketer import MASM
from threading import Lock

inPort = None
doReadInput = False
batched = []
dLock = Lock()

def MIDI_Callback(msg, timestamp):
	global dLock
	global inPort
	global batched
	global doReadInput
	if inPort is not None:
		msgtype, channel = rtmidi2.splitchannel(msg[0])
		if doReadInput: # We want to clear old pending messages but not send them if input is disabled
			if msgtype == rtmidi2.NOTEON or msgtype == rtmidi2.NOTEOFF:
				note, velocity = msg[1], msg[2]
				with dLock:
					if msgtype == rtmidi2.NOTEON and velocity > 0:
						batched.append((f"MIDI_NOTE.{note}", velocity))
					elif msgtype == rtmidi2.NOTEOFF or velocity == 0:
						batched.append((f"MIDI_NOTE.{note}", 0))
		elif MASM.hasDataCheck("MIDI_KEYMAPKEY"):
			if msgtype == rtmidi2.NOTEON:
				note = msg[1]
				MASM.hasDataBool("MIDI_KEYMAPKEY")
				MASM.sendData("MIDI_KEY", note)

def Start():
	global inPort
	try:
		print(f"MIDI inputs: {rtmidi2.get_in_ports()}")
		inPort = rtmidi2.MidiIn()
		inPort.callback = MIDI_Callback
		inPort.open_port()
		print(f"MIDI input open: {inPort}")
	except Exception as e:
		inPort = None
		print(f"Could not open MIDI input: {e}")

def Update():
	global dLock
	global inPort
	global batched
	global doReadInput
	if inPort is not None:
		if doReadInput:
			if MASM.hasDataBool("MIDI_STOP"):
				doReadInput = False
			else:
				with dLock:
					if len(batched) > 0:
						MASM.sendData("MIDI_NOTES", batched)
						batched = []
		elif MASM.hasDataBool("MIDI_START"):
			doReadInput = True

def OnQuit():
	global inPort
	global batched
	if inPort is not None:
		inPort.close_port()
		batched = []