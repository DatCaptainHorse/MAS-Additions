# Changelog #
# 0.1.8 -> 2.0.0
# - Better versioning
# - Using official Submod API
# - Bunch of changeable settings and buttons!
# - Semi-continuous recognition for less freezing
# - New and updated topics
# - Different responses, Monika can tell you to turn on the lights
# - Painful amount of testing, I really hope stuff works..
# 2.0.0 -> 2.0.1
# - Fixes to topics, update script for persistent update

default persistent.submods_dathorse_FDAR_date = None
default persistent.submods_dathorse_FDAR_chosenCamera = 0
default persistent.submods_dathorse_FDAR_todayNotified = False # Don't keep notifying on alltime topic about doing it on same day
default persistent.submods_dathorse_FDAR_allowAccess = False
default persistent.submods_dathorse_FDAR_keepOpen = True # Whether to keep webcam open or only open it for recognition
default persistent.submods_dathorse_FDAR_detectionMethod = "HAAR" # Default to HAAR for faster recognition
default persistent.submods_dathorse_FDAR_detectionTimeout = 10 # 10 seconds should be good enough, user can adjust if needed
default persistent.submods_dathorse_FDAR_memoryTimeout = 5 # 5 seconds of larger data, starting at 100MB (math goes: 100MB * timeout / 5)

init -990 python:
    store.mas_submod_utils.Submod(
        author="DatHorse",
        name="Face Detection and Recognition",
        description=(
            "Adds facial detection and recognition functionality to MAS.\n"
            "Adds 2 topics by itself, 'Webcam' (1-time-only) and\n"
            "'How do I look?' which is visible after first topic in 'Mod' category.\n"
        ),
        version="2.0.1",
        dependencies={
            "Monika After Story Module" : (None, None)
        },
        settings_pane="FDAR_settings_pane",
        version_updates={
            "submods_dathorse_FDAR_v2_0_0": "submods_dathorse_FDAR_v2_0_1"
        }
    )

label submods_dathorse_FDAR_v2_0_0(version="v2_0_0"):
    return

label submods_dathorse_FDAR_v2_0_1(version="v2_0_1"):
    $ mas_stripEVL("submods_dathorse_facedetection_override_monika_playersface", list_pop = True)
    $ mas_stripEVL("submods_dathorse_facedetection_anytime", list_pop = True)
    return

init -990 python:
    import time
    import atexit
    import threading
    # Face Detection and Recognition functions
    class FDAR:
        status = None
        initPrepared = False
        statusThread = None
        statusThreadEvent = threading.Event()
        availableCameras = []
        stateMachine = { "NONE": False, "RECOGNIZING": False, "PREPARING": False, "MEMORIZING": False, "UPDATING_CAMS": False }

        # Set current stateMachine state
        # This is for internal use.
        @staticmethod
        def _setState(statename):
            FDAR.stateMachine = dict.fromkeys(FDAR.stateMachine.viewkeys(), False)
            FDAR.stateMachine[statename] = True

        # Get given state's state
        # This is for internal use.
        @staticmethod
        def _getState(statename):
            for k, v in FDAR.stateMachine.viewitems():
                if k == statename:
                    return v
            return False

        # Get current state
        # This is for internal use.
        @staticmethod
        def _getStateName():
            for k, v in FDAR.stateMachine.viewitems():
                if v:
                    return k
            return "Invalid state"

        # Screen update function
        # This is for internal use.
        @staticmethod
        def _updateLoop():
            coolDots = "."
            lastTime = time.time()
            startTime = time.time()
            loopTimeout = 10
            if not persistent.submods_dathorse_FDAR_keepOpen or not FDAR.initPrepared:
                loopTimeout *= 2 # Some extra time, hoping some webcam doesn't take longer than this to open. TODO: Calculate webcam opening time.

            if FDAR._getState("UPDATING_CAMS"):
                loopTimeout *= 6 # Multiple slow cameras can really slow things down..

            while not FDAR.statusThreadEvent.is_set() and MASM.isWorking() and not FDAR._getState("NONE"):
                if MASM.hasDataBool("FDAR_FAILURE"):
                    FDAR._setState("NONE")
                    FDAR.status = "Preparation failed"
                    renpy.restart_interaction()
                elif MASM.hasDataBool("FDAR_CAMON"):
                    if FDAR.initPrepared:
                        FDAR._setState("NONE")
                        FDAR.status = "Camera opened, ready!"
                    else:
                        FDAR.status = "Camera opened"
                    renpy.restart_interaction()
                elif MASM.hasDataBool("FDAR_MEMORIZE_LOWLIGHT"):
                    FDAR._setState("NONE")
                    FDAR.status = "Not enough light"
                    renpy.restart_interaction()
                elif MASM.hasDataBool("FDAR_MEMORIZE_DONE"):
                    if not FDAR.initPrepared:
                        FDAR.initPrepared = True
                        MASM.sendData("FDAR_MEMORIZE", (False, 3)) # Manually doing this here # TODO: Need somehow to keep cam on so it doesn't need to reopen # TODO: problem anymore?
                    else:
                        FDAR._setState("NONE")
                        FDAR.status = "Prepared, ready!"
                        renpy.restart_interaction()
                elif MASM.hasDataBool("FDAR_NOPREPAREDATA"):
                    if not FDAR.initPrepared: # Don't update data immediately if we are already taking initial one
                        FDAR.initPrepared = True
                elif MASM.hasDataCheck("FDAR_CAMSLIST"):
                    FDAR.availableCameras = MASM.hasDataValue("FDAR_CAMSLIST")
                    FDAR.status = "Available cameras: {}".format(FDAR.availableCameras)
                    renpy.restart_interaction()
                    FDAR._setState("NONE")
                elif time.time() - lastTime > 1.0:
                    FDAR.status = "Please wait{}".format(coolDots)
                    renpy.restart_interaction()
                    if len(coolDots) < 3:
                        coolDots += "."
                    else:
                        coolDots = "."
                    lastTime = time.time()
                elif time.time() - startTime >= loopTimeout: # Assume something failed on timeout
                    FDAR._setState("NONE")
                    FDAR.status = "Timed out"
                    renpy.restart_interaction()
                time.sleep(0.1) # Nep
            FDAR.statusThreadEvent.set() # Just-in-case set so we can reset

        # Starts screen-update thread
        # This is for internal use.
        @staticmethod
        def _startScreenUpdate():
            if FDAR.statusThread is None or FDAR.statusThreadEvent.is_set():
                if FDAR.statusThread is not None and FDAR.statusThread.is_alive():
                    FDAR.statusThreadEvent.set()
                    FDAR.statusThread.join()
                FDAR.statusThreadEvent.clear()
                FDAR.statusThread = threading.Thread(target = FDAR._updateLoop)
                FDAR.statusThread.start()

        # Sets persistents
        # This is for internal use.
        @staticmethod
        @MASM.atStart
        def _applyPersistents():
            if FDAR.statusThread is not None and FDAR.statusThread.is_alive():
                FDAR._atExit()
            # Set defaults
            FDAR.status = None
            FDAR.initPrepared = False
            FDAR._setState("NONE")
            FDAR.availableCameras = []
            FDAR.availableCameras.append(persistent.submods_dathorse_FDAR_chosenCamera)
            # Apply persistents
            FDAR._setCamera(persistent.submods_dathorse_FDAR_chosenCamera)
            FDAR._setKeepOpen(persistent.submods_dathorse_FDAR_keepOpen)
            FDAR._setTimeout(persistent.submods_dathorse_FDAR_detectionTimeout)
            FDAR._setMemoryTimeout(persistent.submods_dathorse_FDAR_memoryTimeout)
            FDAR._setDetectionMethod(persistent.submods_dathorse_FDAR_detectionMethod)
            FDAR._setAllowAccess(persistent.submods_dathorse_FDAR_allowAccess)
            if persistent.submods_dathorse_FDAR_allowAccess:
                FDAR._setState("PREPARING")
                FDAR._startScreenUpdate()
            else:
                FDAR.initPrepared = True
        
        # Closes necessary things at exit
        # This is for internal use.
        @staticmethod
        @atexit.register
        def _atExit():
            FDAR.statusThreadEvent.set()
            FDAR.statusThread.join()

        # Updates FDAR.availableCameras with available, working camera indexes
        @staticmethod
        def _updateAvailableCameras():
            if FDAR._getState("NONE") and MASM.isWorking():
                FDAR._setState("UPDATING_CAMS")
                MASM.sendData("FDAR_GETCAMS")
                FDAR._startScreenUpdate()

        # Changes current camera being used
        @staticmethod
        def _setCamera(camID):
            if FDAR._getState("NONE") and MASM.isWorking():
                MASM.sendData("FDAR_SETCAM", camID)

        # Changes current camera being used
        @staticmethod
        def _switchCamera():
            if FDAR._getState("NONE") and MASM.isWorking():
                try:
                    persistent.submods_dathorse_FDAR_chosenCamera = FDAR.availableCameras[(FDAR.availableCameras.index(persistent.submods_dathorse_FDAR_chosenCamera) + 1) % len(FDAR.availableCameras)]
                except:
                    persistent.submods_dathorse_FDAR_chosenCamera = FDAR.availableCameras[0] if len(FDAR.availableCameras) > 0 else 0
                FDAR._setCamera(persistent.submods_dathorse_FDAR_chosenCamera)

        # Tests chosen camera by turning it on and off
        @staticmethod
        def _testCamera():
            if FDAR._getState("NONE") and MASM.isWorking():
                MASM.sendData("FDAR_TESTCAM")

        # Request to memorize player
        # This is for internal use.
        @staticmethod
        def _memorizePlayer(removeOld = False, duringRecognize = False, overrideTimeout = 0):
            if not FDAR._getState("PREPARING") and persistent.submods_dathorse_FDAR_allowAccess and MASM.isWorking():
                FDAR.status = "Memorize requested"
                renpy.restart_interaction()
                if not duringRecognize and FDAR.initPrepared:
                    FDAR._setState("PREPARING")
                    FDAR._startScreenUpdate()
                MASM.sendData("FDAR_MEMORIZE", (removeOld, overrideTimeout))

        # Sets whether webcam should stay open or not.
        # This is for internal use.
        @staticmethod
        def _setKeepOpen(keepopen):
            if not FDAR._getState("PREPARING") and MASM.isWorking():
                if keepopen and FDAR.initPrepared and persistent.submods_dathorse_FDAR_allowAccess:
                    FDAR.status = "Camera open requested"
                    renpy.restart_interaction()
                    FDAR._setState("PREPARING")
                    FDAR._startScreenUpdate()
                MASM.sendData("FDAR_KEEPOPEN", keepopen)
                persistent.submods_dathorse_FDAR_keepOpen = keepopen

        # Switches whether webcam should stay open or not.
        # This is for internal use.
        @staticmethod
        def _switchKeepOpen(): # TODO: Change during runtime, doesn't start on init
            if not FDAR._getState("PREPARING") and MASM.isWorking():
                if not persistent.submods_dathorse_FDAR_keepOpen:
                    persistent.submods_dathorse_FDAR_keepOpen = True
                else:
                    persistent.submods_dathorse_FDAR_keepOpen = False
                FDAR._setKeepOpen(persistent.submods_dathorse_FDAR_keepOpen)

        # Sets whether webcam access is allowed or not.
        # This is mainly for internal use. However if you wish to have dialogue where Monika changes access herself, it's fine to use this.
        @staticmethod
        def _setAllowAccess(allowed):
            if not FDAR._getState("PREPARING") and MASM.isWorking():
                if FDAR.initPrepared:
                    if allowed:
                        FDAR.status = "Access allowed"
                        renpy.restart_interaction()
                        FDAR._setState("PREPARING")
                        FDAR._startScreenUpdate()
                    else:
                        FDAR.status = "Access not allowed"
                        renpy.restart_interaction()
                MASM.sendData("FDAR_ALLOWACCESS", allowed)
                persistent.submods_dathorse_FDAR_allowAccess = allowed

        # Switches whether webcam access is allowed or not.
        # This is for internal use.
        @staticmethod
        def _switchAllowAccess():
            if not FDAR._getState("PREPARING") and MASM.isWorking():
                if not persistent.submods_dathorse_FDAR_allowAccess:
                    persistent.submods_dathorse_FDAR_allowAccess = True
                else:
                    persistent.submods_dathorse_FDAR_allowAccess = False
                FDAR._setAllowAccess(persistent.submods_dathorse_FDAR_allowAccess)

        # Sets timeout.
        # This is for internal use.
        @staticmethod
        def _setTimeout(timeout):
            if not FDAR._getState("PREPARING") and MASM.isWorking():
                MASM.sendData("FDAR_SETTIMEOUT", timeout)
                persistent.submods_dathorse_FDAR_detectionTimeout = timeout

        # Switches timeout.
        # This is for internal use
        @staticmethod
        def _switchTimeout():
            if not FDAR._getState("PREPARING") and MASM.isWorking():
                if persistent.submods_dathorse_FDAR_detectionTimeout == 5:
                    persistent.submods_dathorse_FDAR_detectionTimeout = 10
                elif persistent.submods_dathorse_FDAR_detectionTimeout == 10:
                    persistent.submods_dathorse_FDAR_detectionTimeout = 15
                elif persistent.submods_dathorse_FDAR_detectionTimeout == 15:
                    persistent.submods_dathorse_FDAR_detectionTimeout = 20
                else:
                    persistent.submods_dathorse_FDAR_detectionTimeout = 5
                FDAR._setTimeout(persistent.submods_dathorse_FDAR_detectionTimeout)

        # Set chose memory timeout
        # This is for internal use.
        @staticmethod
        def _setMemoryTimeout(timeout):
            if not FDAR._getState("PREPARING") and MASM.isWorking():
                MASM.sendData("FDAR_SETMEMORYTIMEOUT", timeout)
                persistent.submods_dathorse_FDAR_memoryTimeout = timeout

        # Switches memory timeout
        # This is for internal use
        @staticmethod
        def _switchMemoryTimeout():
            if not FDAR._getState("PREPARING") and MASM.isWorking():
                if persistent.submods_dathorse_FDAR_memoryTimeout == 3:
                    persistent.submods_dathorse_FDAR_memoryTimeout = 4
                elif persistent.submods_dathorse_FDAR_memoryTimeout == 4:
                    persistent.submods_dathorse_FDAR_memoryTimeout = 5
                elif persistent.submods_dathorse_FDAR_memoryTimeout == 5:
                    persistent.submods_dathorse_FDAR_memoryTimeout = 6
                elif persistent.submods_dathorse_FDAR_memoryTimeout == 6:
                    persistent.submods_dathorse_FDAR_memoryTimeout = 7
                elif persistent.submods_dathorse_FDAR_memoryTimeout == 7:
                    persistent.submods_dathorse_FDAR_memoryTimeout = 8
                elif persistent.submods_dathorse_FDAR_memoryTimeout == 8:
                    persistent.submods_dathorse_FDAR_memoryTimeout = 9
                elif persistent.submods_dathorse_FDAR_memoryTimeout == 9:
                    persistent.submods_dathorse_FDAR_memoryTimeout = 10
                else:
                    persistent.submods_dathorse_FDAR_memoryTimeout = 3
                FDAR._setMemoryTimeout(persistent.submods_dathorse_FDAR_memoryTimeout)

        # Sets detection method, for internal use
        @staticmethod
        def _setDetectionMethod(method):
            if not FDAR._getState("PREPARING") and MASM.isWorking():
                MASM.sendData("FDAR_DETECTIONMETHOD", method)
                persistent.submods_dathorse_FDAR_detectionMethod = method

        # Switches detection, for internal use
        @staticmethod
        def _switchDetectionMethod():
            if not FDAR._getState("PREPARING") and MASM.isWorking():
                if persistent.submods_dathorse_FDAR_detectionMethod == "HAAR":
                    persistent.submods_dathorse_FDAR_detectionMethod = "DNN"
                elif persistent.submods_dathorse_FDAR_detectionMethod == "DNN":
                    persistent.submods_dathorse_FDAR_detectionMethod = "BOTH"
                else:
                    persistent.submods_dathorse_FDAR_detectionMethod = "HAAR"
                FDAR._setDetectionMethod(persistent.submods_dathorse_FDAR_detectionMethod)

        # Just short for FDAR_allowAccess
        # Returns True if player has allowed webcam access or False otherwise
        @staticmethod
        def allowedToRecognize():
            return persistent.submods_dathorse_FDAR_allowAccess

        # If we are able to recognize.
        # Returns False if re-memorize is running, access is disabled or MASM is not working, True otherwise
        @staticmethod
        def canRecognize():
            if FDAR._getState("NONE") and persistent.submods_dathorse_FDAR_allowAccess and MASM.isWorking():
                return True
            else:
                return False

        # Parameter person, name of person to look for, default is "Player"
        # Returns 1 if person's face was recognized or 0 if an error occurred, webcam access is disabled or MASM isn't running. 
        # Can also return -1 if low-light is an issue, -2 if waiting needs to be done or -3 if timeout was hit (only returned once).
        lightTime = None
        timeoutTime = None
        extraTimeOnce = False
        timedOutOnce = False
        keepOpenTimedOutOnce = False
        detectionTimeout = None
        @staticmethod
        def canSee(person = "Player"):
            if FDAR.canRecognize():
                FDAR.detectionTimeout = persistent.submods_dathorse_FDAR_detectionTimeout
                if not persistent.submods_dathorse_FDAR_keepOpen:
                    FDAR.detectionTimeout *= 2 # Extra detection time when webcam isn't kept open
                    
                if FDAR._getStateName() == "NONE":
                    if not FDAR.keepOpenTimedOutOnce:
                        MASM.sendData("FDAR_RECOGNIZEONCE", person)
                    FDAR._setState("RECOGNIZING")
                    FDAR.timeoutTime = time.time()
                    FDAR.extraTimeOnce = False
                    FDAR.timedOutOnce = False
                    FDAR.lightTime = None

                while time.time() - FDAR.timeoutTime < FDAR.detectionTimeout and MASM.isWorking():
                    if FDAR._getState("MEMORIZING"):
                        if MASM.hasDataBool("FDAR_MEMORIZE_DONE"):
                            FDAR._setState("NONE")
                            return -2
                        elif MASM.hasDataBool("FDAR_MEMORIZE_LOWLIGHT") and FDAR.lightTime is None:
                            FDAR._memorizePlayer(duringRecognize = True) # Keep trying
                            FDAR.lightTime = time.time()
                            return -1
                        elif FDAR.lightTime is not None and time.time() - FDAR.lightTime > 3: # Return back to "this might take a while" if lights are good now
                            FDAR.lightTime = None
                            return -2
                    elif FDAR._getState("RECOGNIZING"):
                        if MASM.hasDataBool("FDAR_NOTMEMORIZED"):
                            FDAR._setState("MEMORIZING")
                            FDAR._memorizePlayer(duringRecognize = True)
                            if not FDAR.extraTimeOnce:
                                FDAR.extraTimeOnce = True
                                FDAR.timeoutTime += persistent.submods_dathorse_FDAR_memoryTimeout # Some extra time
                                return -2
                        elif MASM.hasDataBool("FDAR_LOWLIGHT") and FDAR.lightTime is None:
                            FDAR.lightTime = time.time()
                            return -1
                        elif FDAR.lightTime is not None and time.time() - FDAR.lightTime > 3: # Low-light resolved probably..
                            FDAR.lightTime = None
                            return -2
                        elif MASM.hasDataBool("FDAR_FAILURE"):
                            MASM.hasDataBool("FDAR_FAILURE") # Clear out possible old result just in case
                            FDAR._setState("NONE")
                            FDAR.keepOpenTimedOutOnce = False
                            FDAR.timedOutOnce = False
                            return 0
                        elif MASM.hasDataValue("FDAR_RECOGNIZED") == person:
                            MASM.hasDataBool("FDAR_RECOGNIZED") # And here..
                            FDAR._setState("NONE")
                            FDAR.keepOpenTimedOutOnce = False
                            FDAR.timedOutOnce = False
                            return 1

                    time.sleep(0.1) # Just to ease up on the loop

                FDAR._setState("NONE")
                if not FDAR.timedOutOnce and MASM.isWorking():
                    if not persistent.submods_dathorse_FDAR_keepOpen and not FDAR.keepOpenTimedOutOnce:
                        FDAR.keepOpenTimedOutOnce = True # Webcam opening can take time # TODO: Check dynamically when open?
                        return -2
                    else:
                        FDAR.timedOutOnce = True
                        FDAR.timeoutTime = time.time() # Reset timer
                        return -3 # Return timeout only once
                else:
                    MASM.sendData("FDAR_RECOGNIZESTOP")
                    FDAR.keepOpenTimedOutOnce = False
                    FDAR.extraTimeOnce = False
                    FDAR.timedOutOnce = False
                    FDAR.lightTime = None
                    return 0 # Otherwise fail
            else:
                return 0

screen FDAR_settings_pane():
    python:
        submods_screen = store.renpy.get_screen("submods", "screens")
        if submods_screen:
            _tooltip = submods_screen.scope.get("tooltip", None)
        else:
            _tooltip = None

        if FDAR.status is not None:
            statusStr = FDAR.status
        else:
            statusStr = "Not ready"

        if persistent.submods_dathorse_FDAR_detectionMethod == "HAAR":
            detectStr = "Fast"
        elif persistent.submods_dathorse_FDAR_detectionMethod == "DNN":
            detectStr = "Fancy"
        else:
            detectStr = "Both"

        if persistent.submods_dathorse_FDAR_keepOpen:
            doubleStr = ""
        else:
            doubleStr = " (doubled)"

    vbox:
        box_wrap False
        xfill True
        xmaximum 1000
        style_prefix "check"

        text "FDAR Status: [statusStr]"
        text "FDAR State: {}".format(FDAR._getStateName()) # TODO: Debug fancy check

        hbox:
            style_prefix "generic_fancy_check"
            if _tooltip:
                textbutton _("Allow webcam access"):
                    action Function(FDAR._switchAllowAccess)
                    selected persistent.submods_dathorse_FDAR_allowAccess
                    hovered SetField(_tooltip, "value", "Toggle whether to allow access to your webcam.")
                    unhovered SetField(_tooltip, "value", _tooltip.default)
            else:
                textbutton _("Allow webcam access"):
                    action Function(FDAR._switchAllowAccess)
                    selected persistent.submods_dathorse_FDAR_allowAccess
        
        if _tooltip:
            textbutton _("Refresh available webcams"):
                action Function(FDAR._updateAvailableCameras)
                hovered SetField(_tooltip, "value", "Gets working webcams for selection. Will take some time.")
                unhovered SetField(_tooltip, "value", _tooltip.default)
        else:
            textbutton _("Refresh available webcams"):
                action Function(FDAR._updateAvailableCameras)

        hbox:
            if _tooltip:
                textbutton _("Chosen webcam: {}".format(persistent.submods_dathorse_FDAR_chosenCamera)):
                    action Function(FDAR._switchCamera)
                    hovered SetField(_tooltip, "value", "Currently chosen webcam, use the test button to check if it's the right one.")
                    unhovered SetField(_tooltip, "value", _tooltip.default)
            else:
                textbutton _("Chosen webcam: {}".format(persistent.submods_dathorse_FDAR_chosenCamera)):
                    action Function(FDAR._switchCamera)

            if _tooltip:
                textbutton _("Test"):
                    action Function(FDAR._testCamera)
                    hovered SetField(_tooltip, "value", "Test if your chosen webcam is the correct one. When clicked check if webcam light turns on momentarily.")
                    unhovered SetField(_tooltip, "value", _tooltip.default)
            else:
                textbutton _("Test"):
                    action Function(FDAR._testCamera)

        hbox:
            style_prefix "generic_fancy_check"
            if _tooltip:
                textbutton _("Keep webcam open"):
                    action Function(FDAR._switchKeepOpen)
                    selected persistent.submods_dathorse_FDAR_keepOpen
                    hovered SetField(_tooltip, "value", "Toggle whether webcam should stay open even if recognition is not happening. Keep this on if your webcam opens slowly.")
                    unhovered SetField(_tooltip, "value", _tooltip.default)
            else:
                textbutton _("Keep webcam open"):
                    action Function(FDAR._switchKeepOpen)
                    selected persistent.submods_dathorse_FDAR_keepOpen
                    
        if _tooltip:
            textbutton _("Recognition method: {}".format(detectStr)):
                action Function(FDAR._switchDetectionMethod)
                hovered SetField(_tooltip, "value", ("Fast is better with low-light but Monika may have trouble seeing you.\n"
                                                "Fancy requires more CPU and is worse in low-light but Monika can see you better.\n"
                                                "Both switches between Fast and Fancy by itself, having benefits of both methods but using more CPU."))
                unhovered SetField(_tooltip, "value", _tooltip.default)
        else:
            textbutton _("Recognition method: {}".format(detectStr)):
                action Function(FDAR._switchDetectionMethod)

        hbox:
            if _tooltip:
                textbutton _("Recognize timeout: {}s{}".format(persistent.submods_dathorse_FDAR_detectionTimeout, doubleStr)):
                    action Function(FDAR._switchTimeout)
                    hovered SetField(_tooltip, "value", "How long will Monika try to see you for before giving up. This is doubled if webcam isn't kept open.")
                    unhovered SetField(_tooltip, "value", _tooltip.default)
            else:
                textbutton _("Recognize timeout: {}s{}".format(persistent.submods_dathorse_FDAR_detectionTimeout, doubleStr)):
                    action Function(FDAR._switchTimeout)

            if _tooltip:
                textbutton _("Memorization stop after: {}s".format(persistent.submods_dathorse_FDAR_memoryTimeout)):
                    action Function(FDAR._switchMemoryTimeout)
                    hovered SetField(_tooltip, "value", "How long will Monika memorize your look for, longer is better but\n uses more space (limited to 60MB at 3s - 200MB at 10s)")
                    unhovered SetField(_tooltip, "value", _tooltip.default)
            else:
                textbutton _("Memorization stop after: {}s".format(persistent.submods_dathorse_FDAR_memoryTimeout)):
                    action Function(FDAR._switchMemoryTimeout)

        hbox:
            if persistent.submods_dathorse_FDAR_allowAccess:
                if _tooltip:
                    textbutton _("Update Memory"):
                        action Function(FDAR._memorizePlayer, False, False, 3)
                        hovered SetField(_tooltip, "value", "Adds your current look to Monika's memory so she can see you easier.")
                        unhovered SetField(_tooltip, "value", _tooltip.default)
                else:
                    textbutton _("Update Memory"):
                        action Function(FDAR._memorizePlayer, False, False, 3)

                if _tooltip:
                    textbutton _("Re-Memorize"):
                        action Function(FDAR._memorizePlayer, True)
                        hovered SetField(_tooltip, "value", "Complete re-memorization if you have issues with Monika seeing you no matter what.")
                        unhovered SetField(_tooltip, "value", _tooltip.default)
                else:
                    textbutton _("Re-Memorize"):
                        action Function(FDAR._memorizePlayer, True)
            else:
                textbutton _("Update Memory (disabled)"):
                    action None
                    
                textbutton _("Re-Memorize (disabled)"):
                    action None
