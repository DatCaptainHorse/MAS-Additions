# Changelog #
# 2.0.0
# - Reworked for MAS official Submod framework, made versioning make more sense by shifting to major from minor versioning.
# - UDP is now default, as it allows for connectionless data transfer without headaches of checking whether TCP connected or not.
# - We are no longer checking whether MASM is running as checking it's state was unreliable.
# - Removed remData, well keep a short array of recently received data and discard any old or looked up data.
# - Renamed to short and simple MASM for less word spaghetti, also some functions to make more sense.
# - Thread locks that hopefully fix any issues with reading data partially from somewhere before all is received.
init -990 python in mas_submod_utils:
    Submod(
        author="DatHorse",
        name="MASM",
        description="Communicates with external process for added functionality.",
        version="2.0.0",
        dependencies={},
        settings_pane="MASM_setting_pane",
        version_updates={}
    )

    import os
    import re
    import time
    import atexit
    import socket
    import threading
    import subprocess
    
    # Some global variables for debugging and whatnot
    MASM_processPID = None
    MASM_status = "Not Found"

    class MASM:
        data = []
        dictData = {}
        subProc = None
        serverUDP = None
        commThread = None
        commLock = threading.Lock()

        def connectMASM(self):
            if MASM.serverUDP is None:
                MASM.serverUDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                MASM.serverUDP.settimeout(0.1)
                MASM.serverUDP.bind(('127.0.0.1', 24488))
            
            if MASM.commThread is None:
                MASM.commThread = threading.Thread(target = self.communicationLoop)
                MASM.commThread.setDaemon(True)
                MASM.commThread.start()

        def communicationLoop(self):
            with MASM.commLock:
                received = None
                try:
                    received, addr = MASM.serverUDP.recvfrom(128)
                except socket.error: # No data
                    pass

                if received is not None:
                    #renpy.log("MASM received data: {}".format(received))
                    received = received.decode('utf-8')
                    if received.startswith('{{'):
                        res = re.search('{{(.*) : (.*)}}', received)
                        dictData[res.group(1)] = bool(res.group(2))
                    else:
                        if len(MASM.data) >= 16: # Keeping received data somewhat fresh
                            MASM.data.pop()
                        if received in MASM.data: # Don't allow duplicates but remove older copy so we get a refresher
                            MASM.data.remove(receive)
                        MASM.data.append(received)
                
        @staticmethod
        def hasData(dat):
            with MASM.commLock:
                if dat in MASM.data:
                    MASM.data.remove(dat)
                    return True
                else:
                    return False

        @staticmethod
        def sendData(toSend):
            if MASM.subProc is not None:
                if MASM.serverUDP is not None:
                    MASM.serverUDP.sendto(toSend.encode('utf-8'), ('127.0.0.1', 24489))

        @staticmethod
        def dictHas(dictKey):
            with MASM.commLock:
                dictData.get(dictKey, False)

        @staticmethod
        def dictSend(sendKey, sendVal):
            if MASM.subProc is not None:
                dictData[sendKey] = sendVal
                toSend = ('{{' + sendKey + ':' + sendVal + '}}')
                if MASM.serverUDP is not None:
                    MASM.serverUDP.sendto(toSend.encode('utf-8'), ('127.0.0.1', 24489))

        def exiting(self):
            if MASM.subProc is not None:
                MASM.subProc.kill() # We don't want to leave dangling subprocesses behind at all

        def startMASM(self):
            global MASM_status
            global MASM_processPID
            MASMpath = None
            for root, dirs, files in os.walk('.'):
                for name in files:
                    if name == 'MASM.exe':
                        MASMpath = os.path.abspath(os.path.join(root, name))
                        break

            if MASMpath is not None: # Open MASM subprocess
                MASM_status = MASMpath
                try:
                    #if renpy.windows: # If we are running on Windows..
                    MASM.subProc = subprocess.Popen(MASMpath)
                    #elif renpy.linux or renpy.macintosh: # Linux / Mac..
                    #    MASM.subProc = subprocess.Popen(MASMpath)
                    atexit.register(self.exiting) # Because subprocesses
                    MASM_processPID = MASM.subProc.pid
                except:
                    return False
            return True

    # Create default MASM communication instance
    communicator = MASM()
    if communicator.startMASM():
        communicator.connectMASM()

init 10 python:
    # Not sure how to do this or if it's possible with official Submod framework yet
    #if isAdditionFirstRun("MASMC"):
    #    MASM.sendData("first")
    #else:
    #    MASM.sendData("notFirst")

    mas_submod_utils.MASM.sendData("Are you awake?")

screen MASM_setting_pane():
    python:
        subproc_PID = "Subprocess PID: None"
        foundPath = "MASM status: %s" % mas_submod_utils.MASM_status
        if mas_submod_utils.MASM_processPID is not None:
            subproc_PID = "Subprocess PID: %d" % mas_submod_utils.MASM_processPID

        def test_packet():
            mas_submod_utils.MASM.sendData("Anime Tiddies")

    vbox:
        box_wrap False
        xfill True
        xmaximum 1000

        vbox:
            style_prefix "check"
            box_wrap False

            text subproc_PID size 15
            text foundPath size 15
            textbutton _("MASM Test Packet") action Function(test_packet)