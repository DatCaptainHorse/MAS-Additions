# Changelog #
# 2.0.0 -> 2.1.0
# - Did things better now that I got a better understanding of the Submod API
# - Readded "canUse" as "isWorking" checking function as it's quite important incase MASM fails to open
# - Less global variables so things are better contained
# - No more 'anime tiddies' test packet, unfortunately
# - Cleaned up initialization and exit functions so MASM can be restarted at runtime if needed
# - Raised receive sizes to 256 for possibly larger data
# - Replaced data lists with single dictionary to keep things cleaner
# - Packets are dumped tuples as they are fast to construct and simple to reconstruct
# - Subprocess console hiding on Windows
# - Bunch of painful testing so stuff is stable, might still have a rare edge-case somewhere..
# - Binary is no longer hogging the CPU
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
            "This submod by alone doesn't do much.\n"
        ),
        version="2.1.0",
        settings_pane="MASM_settings_pane",
        version_updates={}
    )

init -991 python:
    import os
    import re
    import stat
    import time
    import json
    import errno
    import atexit
    import socket
    import threading
    import subprocess
    # MASM class, communicates with external process using sockets for added functionality
    class MASM:
        initialized = 0 # 0 is none, 1 is socket, 2 is thread, 3 is subprocess (complete)
        status = None
        path = None
        data = {}
        timing = 0.0
        startTime = 0.0
        subProc = None
        commLock = None
        commThread = None
        atStartCalls = []
        communicationRun = None
        serverConnection = None
        # Opens MASM subprocess, for internal use
        @staticmethod
        def _openMASM():
            if MASM.initialized < 3:
                MASMroot = None
                for root, dirs, files in os.walk("."):
                    for name in files:
                        if name == "MASM.exe" or name == "MASM":
                            MASM.path = os.path.abspath(os.path.join(root, name))
                            MASMroot = os.path.abspath(root)
                            if renpy.linux: # Set exec permissions so the binary loads up properly on Linux
                                st = os.stat(MASM.path)
                                os.chmod(MASM.path, st.st_mode | stat.S_IEXEC)
                            break

                if MASM.path: # Open MASM subprocess
                    try:
                        sInfo = None
                        if renpy.windows: # Hide external cmd popup in Windows
                            sInfo = subprocess.STARTUPINFO()
                        #    sInfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                        MASM.subProc = subprocess.Popen(MASM.path, startupinfo=sInfo)
                        MASM.status = "Subprocess was created"
                    except:
                        MASM.status = "Unable to create subprocess"
                        return False
                else:
                    MASM.status = "Path not found"
                    return False
                MASM.initialized = 3
            return True

        # Creates MASM sockets
        @staticmethod
        def _connectMASM():
            if MASM.initialized < 1:
                try:
                    MASM.serverConnection = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    MASM.serverConnection.settimeout(0.1) # Timeout blocks, but we want to exit thread at some point
                    MASM.serverConnection.bind(("127.0.0.1", 24488))
                    MASM.status = "Socket was created"
                except:
                    MASM.status = "Unable to create socket"
                    return False
                MASM.initialized = 1
            return True

        # Starts MASM thread, for internal use
        @staticmethod
        def _startThreadMASM():
            if MASM.initialized < 2:
                try:
                    MASM.commLock = threading.Lock()
                    MASM.communicationRun = threading.Event()
                    MASM.commThread = threading.Thread(target = MASM._communicationLoop)
                    MASM.commThread.daemon = True
                    MASM.commThread.start()
                    MASM.status = "Thread was started"
                except:
                    MASM.status = "Unable to create thread"
                    return False
                MASM.initialized = 2
            return True
        
        # Stops MASM, for internal use
        @staticmethod
        @atexit.register
        def _stopMASM():
            if MASM.initialized >= 2:
                MASM.communicationRun.set() # Set stop flag, thread is daemon so it will die even if this doesn't succeed
            if MASM.initialized >= 1:
                try:
                    MASM.serverConnection.close()
                except:
                    pass # Shouldn't happen anyways
            if MASM.initialized >= 3:
                try:
                    MASM.subProc.terminate() # Try kind form of termination first
                    time.sleep(0.25) # Slight delay so signal can pass
                    if MASM.subProc.poll():
                        MASM.subProc.kill() # If that doesn't work, take a shot
                    MASM.subProc = None
                except:
                    pass # At this point just.. yea
                    
            MASM.initialized = 0
            MASM.status = None

        # Communication loop for the thread, for internal use
        @staticmethod
        def _communicationLoop():
            while not MASM.communicationRun.is_set():
                try:
                    recv, addr = MASM.serverConnection.recvfrom(256)
                    if recv is not None:
                        recv = json.loads(recv.decode("utf-8"))
                        if recv[0] == "pong":
                            MASM.timing = (time.time() - MASM.startTime) * 1000.0
                        if recv[0] == "MASM_READY":
                            MASM.status = "Ready!"
                            for atStart in MASM.atStartCalls:
                                atStart()
                            MASM.timing = (time.time() - MASM.startTime) * 1000.0
                        else:
                            with MASM.commLock:
                                MASM.data[recv[0]] = recv[1]
                except socket.timeout:
                    continue # No data received
                except socket.error:
                    pass # Probably due to subprocess dying

                if MASM.subProc.poll() is not None: # If subprocess died prematurely
                    MASM.status = "Subprocess closed"
                    MASM.initialized = 1
                    MASM.communicationRun.set()

        # Does a full stop and start of MASM, for internal use
        @staticmethod
        def _startFull():
            MASM._stopMASM()
            MASM.startTime = time.time()
            if MASM._connectMASM():
                if MASM._startThreadMASM():
                    MASM._openMASM()

        @staticmethod
        def _ping():
            if MASM.isWorking() and MASM.serverConnection is not None:
                MASM.startTime = time.time()
                MASM.serverConnection.sendto(json.dumps(("ping", True)).encode("utf-8"), ("127.0.0.1", 24489))

        # Finds data by starting string, like startswith() for data
        # Returns tuple of data string and value if succesful, tuple (None, None) otherwise
        @staticmethod
        def hasDataWith(dictKey):
            res = None
            with MASM.commLock:
                try:
                    res = next(((k, v) for k, v in MASM.data.viewitems() if k.startswith(dictKey)), None)
                    if res[0] is not None:
                        del MASM.data[res[0]]
                except:
                    res = (None, None)
            return res

        # Returns data's value if found by string, None if failed
        @staticmethod
        def hasDataValue(dictKey):
            res = None
            with MASM.commLock:
                res = MASM.data.get(dictKey, None)
                if res is not None:
                    del MASM.data[dictKey]
            return res

        # Returns True or False depending if data with string was found
        @staticmethod
        def hasDataBool(dictKey):
            res = False
            with MASM.commLock:
                if dictKey in MASM.data:
                    del MASM.data[dictKey] # keep dict tidy and garbage-collected
                    res = True
            return res

        # Sends data, sendKey is data's string identifier, sendValue is optional value to send alongside
        @staticmethod
        def sendData(sendKey, sendValue = True):
            if MASM.isWorking() and MASM.serverConnection is not None:
                MASM.serverConnection.sendto(json.dumps((sendKey, sendValue)).encode("utf-8"), ("127.0.0.1", 24489))

        # Returns True or False depending if MASM was initialized fully and is currently working
        @staticmethod
        def isWorking():
            if MASM.initialized == 3:
                return True
            else:
                return False

        # Decorator, adds function to be called at MASM startup, useful for sending persistent data on startup
        # Functions with this decorator should be initialized at -990
        @staticmethod
        def atStart(func):
            MASM.atStartCalls.append(func)

init -989 python:
    # Initialize Monika After Story Module
    # Done after submods have had their decorators set so we can call them
    MASM._startFull()
    
screen MASM_settings_pane():
    python:
        submods_screen = store.renpy.get_screen("submods", "screens")
        if submods_screen:
            _tooltip = submods_screen.scope.get("tooltip", None)
        else:
            _tooltip = None

        if MASM.subProc:
            subprocPID = MASM.subProc.pid
        else:
            subprocPID = 0

        if MASM.status:
            statusStr = MASM.status
        else:
            statusStr = "Not Ready"

        strTiming = "{:.2f}".format(MASM.timing)
        strPath = str(MASM.path)
    vbox:
        box_wrap False
        xfill True
        xmaximum 1000
        style_prefix "check"

        text "MASM Status: [statusStr]"
        text "MASM Startup/Ping time: [strTiming]ms"
        text "MASM PID: [subprocPID]"
        text "MASM Path: [strPath]"
        
        hbox:
            if _tooltip:
                textbutton _("Test Packet"):
                    action Function(MASM._ping)
                    hovered SetField(_tooltip, "value", "For debugging purposes, sends a ping packet")
                    unhovered SetField(_tooltip, "value", _tooltip.default)
            else:
                textbutton _("Test Packet"):
                    action Function(MASM._ping)
            
            if _tooltip:
                textbutton _("Restart MASM"):
                    action Function(MASM._startFull)
                    hovered SetField(_tooltip, "value", "For debugging purposes, restarts MASM")
                    unhovered SetField(_tooltip, "value", _tooltip.default)
            else:
                textbutton _("Restart MASM"):
                    action Function(MASM._startFull)