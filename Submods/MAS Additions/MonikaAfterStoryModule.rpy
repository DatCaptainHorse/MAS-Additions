# Changelog #
# 2.0.0 -> 2.1.0
# - Did things better now that I got a better understanding of the API
# - Readded "canUse" as "isWorking" checking function as it's quite important incase MASM fails to open
# - Less global variables so things are better contained
# - No more anime tiddies test packet, unfortunately
# 2.0.0
# - Reworked for MAS official Submod framework, made versioning make more sense by shifting to major from minor versioning.
# - UDP is now default, as it allows for connectionless data transfer without headaches of checking whether TCP connected or not.
# - We are no longer checking whether MASM is running as checking it's state was unreliable.
# - Removed remData, well keep a short array of recently received data and discard any old or looked up data.
# - Renamed to short and simple MASM for less word spaghetti, also some functions to make more sense.
# - Thread locks that hopefully fix any issues with reading data partially from somewhere before all is received.
init -990 python:
    store.mas_submod_utils.Submod(
        author="DatHorse",
        name="Monika After Story Module",
        description=(
            "Communicates with external process for Python 3 support.\n"
            "This submod by alone doesn't do much."
        ),
        version="2.1.0",
        settings_pane="MASM_settings_pane",
        version_updates={}
    )

init -991 python:
    import os
    import re
    import time
    import atexit
    import socket
    import threading
    import subprocess

    class MASM:
        initialized = 0 # 0 is none, 1 is subprocess, 2 is socket, 3 is thread (complete)
        status = None
        path = None
        data = []
        dictData = {}
        subProc = None
        socketUDP = None
        commThread = None
        communicationRun = None
        commLock = None
        latency = 0.0
        startTime = 0.0

        @staticmethod
        def startMASM():
            for root, dirs, files in os.walk("."):
                for name in files:
                    if name == "MASM.exe" or name == "MASM":
                        MASM.path = os.path.abspath(os.path.join(root, name))
                        break

            if MASM.path: # Open MASM subprocess
                try:
                    MASM.subProc = subprocess.Popen(MASM.path)
                    MASM.status = "Subprocess was created"
                    MASM.initialized = 1
                except:
                    MASM.status = "Unable to create subprocess"
                    return False
            else:
                MASM.status = "Path not found"
                return False
            return True

        @staticmethod
        def connectMASM():
            if not MASM.socketUDP:
                try:
                    MASM.socketUDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    MASM.socketUDP.settimeout(0.1) # Timeout blocks, but we want to exit thread at some point
                    MASM.socketUDP.bind(("127.0.0.1", 24488))
                    MASM.status = "Socket was created"
                    MASM.initialized = 2
                except:
                    MASM.status = "Unable to create socket"
                    return False
            return True

        @staticmethod
        def startThreadMASM():
            if not MASM.commThread:
                try:
                    MASM.commLock = threading.Lock()
                    MASM.communicationRun = threading.Event()
                    MASM.commThread = threading.Thread(target = MASM.communicationLoop)
                    MASM.commThread.daemon = True
                    MASM.commThread.start()
                    MASM.status = "Thread was started"
                    MASM.initialized = 3
                except:
                    MASM.status = "Unable to create thread"
                    return False
            return True
        
        @atexit.register
        def exitMASM():
            if MASM.initialized == 3:
                MASM.communicationRun.set() # Set stop flag, thread is daemon so it will die eventually
            if MASM.initialized >= 2:
                try:
                    MASM.socketUDP.close()
                except:
                    pass # Shouldn't happen anyways
                else:
                    MASM.socketUDP = None
            if MASM.initialized >= 1:
                try:
                    MASM.subProc.terminate() # Try termination first
                    MASM.subProc.kill() # If that doesn't work, have it killed
                except:
                    pass # At this point just.. yea
                else:
                    MASM.subProc = None
            MASM.initialized = 0

        # Has to be static for receiving to work
        @staticmethod
        def communicationLoop():
            while not MASM.communicationRun.is_set():
                received = None
                try:
                    recv, addr = MASM.socketUDP.recvfrom(128)
                    received = recv.decode("utf-8")
                except socket.timeout:
                    pass # No data received
                except socket.error:
                    pass # For now just pass
                if received:
                    MASM.commLock.acquire()
                    if received.startswith("{{"):
                        res = re.search("{{(.*):(.*)}}", received)
                        dictData[res.group(1)] = str(res.group(2)).lower() in ("True", "true", "1")
                    elif received != "pong":
                        if received in MASM.data: # Don't allow duplicates but remove older copy so we get a refresher
                            MASM.data.remove(received)
                        MASM.data.append(received)
                    else:
                        MASM.latency = (time.time() - MASM.startTime) * 1000
                    MASM.commLock.release()
                else:
                    MASM.commLock.acquire()
                    if len(MASM.data) >= 16: # Keeping received data somewhat fresh
                        MASM.data.pop()
                    MASM.commLock.release()
                    time.sleep(0.01) # Don't hog the CPU

        @staticmethod
        def hasData(dat):
            res = False
            MASM.commLock.acquire()
            if dat in MASM.data:
                MASM.data.remove(dat)
                res = True
            MASM.commLock.release()
            return res
        
        @staticmethod
        def hasDataWith(dat):
            res = None
            MASM.commLock.acquire()
            for fDat in MASM.data:
                if dat in fDat:
                    MASM.data.remove(fDat)
                    res = fDat
            MASM.commLock.release()
            return res

        @staticmethod
        def sendData(toSend):
            if MASM.isWorking():
                if toSend == "ping":
                    MASM.startTime = time.time()
                MASM.socketUDP.sendto(toSend.encode("utf-8"), ("127.0.0.1", 24489))

        @staticmethod
        def dictHas(dictKey):
            MASM.commLock.acquire()
            res = dictData.get(dictKey, False)
            MASM.commLock.release()
            return res

        @staticmethod
        def dictSend(sendKey, sendVal):
            if MASM.isWorking():
                MASM.commLock.acquire()
                dictData[sendKey] = sendVal
                MASM.commLock.release()
                toSend = ("{{" + sendKey + ":" + sendVal + "}}")
                MASM.socketUDP.sendto(toSend.encode("utf-8"), ("127.0.0.1", 24489))

        @staticmethod
        def isWorking():
            if MASM.initialized == 3:
                return True
            else:
                return False

    # Initialize Monika After Story Module
    if MASM.startMASM():
        if MASM.connectMASM():
            if MASM.startThreadMASM():
                MASM.status = "Ready!"

screen MASM_settings_pane():
    python:
        submods_screen = store.renpy.get_screen("submods", "screens")
        if submods_screen:
            _tooltip = submods_screen.scope.get("tooltip", None)
        else:
            _tooltip = None

        subprocPID = MASM.subProc.pid
        strPath = str(MASM.path)
    vbox:
        box_wrap False
        xfill True
        xmaximum 1000
        style_prefix "check"

        text "MASM Status: [MASM.status]"
        text "MASM Latency: [MASM.latency]ms"
        text "MASM PID: [subprocPID]"
        text "MASM Path: [strPath]"
        
        if _tooltip:
            textbutton _("Test Packet"):
                action Function(MASM.sendData, "ping")
                hovered SetField(_tooltip, "value", "For debugging purposes, sends a test packet to MASM process")
                unhovered SetField(_tooltip, "value", _tooltip.default)
        else:
            textbutton _("Test Packet"):
                action Function(MASM.sendData, "ping")