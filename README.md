# MAS-Additions

Additions for Monika After Story mod for DDLC

https://github.com/Monika-After-Story/MonikaModDev


# Additions
* Core, core functionality, enables adding of additions and enabling/disabling them using ingame UI or ini file.

* MASM, MAS Module is an external program which enables the use of Python 3 and Lua, along with some extra features such as 3D audio (3D audio position is currently broken).

* Face D&R, adds a new 'Webcamera' topic which allows Monika to see the player using OpenCV. v1.0.6 is currently only capable of face detection since earlier features broke with Python 3.8 beta upgrade.

* MIDI, adds MIDI functionality, routes MIDI input to MAS piano keys.

**You always need Core and MASM to be installed for most other things to work.**


## Installing - Core
1. Copy "python-packages", "screens.rpyc" and "zz_additions.rpyc" files into DDLC game folder.


## Installing - MASM
**Requires: Core**

1. Copy "zz_additions_MASM_communicator.rpyc" file and "MASM" folder into DDLC game folder.

2. Copy "MASM.exe", "OpenAL32.dll" and "python38.dll" files from MASM_Binaries folder into "MASM" folder in the DDLC game folder.


## Installing - FaceDetectionRecognition
**Requires: Core, MASM**

1. Copy "zz_additions_face_detection.rpyc" file and "MASM" folder into DDLC game folder.


## Installing - MIDI
**Requires: Core, MASM**

1. Copy "zz_pianokeys.rpyc" file and MASM folder into DDLC game folder, replace the existing "zz_pianokeys.rpyc" file.

# Reporting bugs and issues

Please report any bugs and issues you may have to DatHorse#9516 on Discord
