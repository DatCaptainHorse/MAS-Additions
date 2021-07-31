# Changelog #
# 0.1.8 -> 2.0.0
# - Better versioning
# - Using official Submod API
# - Bunch of changeable settings and buttons!
# - Semi-continuous recognition for less freezing
# - New and updated topics
# - Different responses, Monika can tell you to turn on the lights
# - Painful amount of testing, I really hope stuff works..

default persistent.submods_dathorse_FDAR_date = None
default persistent.submods_dathorse_FDAR_todayNotified = False # Don't keep notifying on alltime topic about doing it on same day
default persistent.submods_dathorse_FDAR_allowAccess = False
default persistent.submods_dathorse_FDAR_keepOpen = True # Whether to keep webcam open or only open it for recognition
default persistent.submods_dathorse_FDAR_detectionMethod = "HAAR" # Default to HAAR for faster recognition
default persistent.submods_dathorse_FDAR_detectionTimeout = 10 # 10 seconds should be good enough, user can adjust if needed
default persistent.submods_dathorse_FDAR_memoryTimeout = 3 # 3 seconds of larger data, starting at 60MB (math goes: 100MB * timeout / 5)

init -990 python:
    store.mas_submod_utils.Submod(
        author="DatHorse",
        name="Face Detection and Recognition",
        description=(
            "Adds facial detection and recognition functionality to MAS.\n"
            "Adds 2 topics by itself, 'Webcam' (1-time-only) and\n"
            "'How do I look?' which is visible after first topic within 'Mod' category\n"
        ),
        version="2.0.0",
        dependencies={
            "Monika After Story Module" : (None, None)
        },
        settings_pane="FDAR_settings_pane",
        version_updates={}
    )

init -990 python:
    import time
    import atexit
    import threading
    # Face Detection and Recognition functions
    class FDAR:
        status = None
        initPrepared = False
        workaroundAllowState = False
        statusThread = None
        statusThreadEvent = threading.Event()
        stateMachine = { "RECOGNIZING": False, "PREPARING": False, "MEMORIZING": False, "CAMCHANGE": False }
        # Screen update function
        # This is for internal use.
        # TODO: Timeout for preparation!
        @staticmethod
        def _updateLoop():
            coolDots = "."
            lastTime = time.time()
            startTime = time.time()
            prepareTimeout = 10
            if not persistent.submods_dathorse_FDAR_keepOpen:
                prepareTimeout *= 2 # Some extra time not kept open, if your webcam takes longer than this to open I'm sorry you have to deal with that.
            while not FDAR.statusThreadEvent.is_set() and MASM.isWorking() and (FDAR.stateMachine["PREPARING"] or FDAR.stateMachine["CAMCHANGE"]):
                if FDAR.stateMachine["CAMCHANGE"]:
                    if MASM.hasDataBool("FDAR_FAILURE"):
                        FDAR.stateMachine["CAMCHANGE"] = False
                        FDAR.status = "Failed to open camera"
                        renpy.restart_interaction()
                    elif MASM.hasDataBool("FDAR_SUCCESS"):
                        FDAR.stateMachine["CAMCHANGE"] = False
                        FDAR.status = "Ready!"
                        renpy.restart_interaction()
                    elif time.time() - lastTime > 1.0:
                        FDAR.status = "Opening camera, please wait{}".format(coolDots)
                        renpy.restart_interaction()
                        if len(coolDots) < 3:
                            coolDots += "."
                        else:
                            coolDots = "."
                        lastTime = time.time()
                    elif time.time() - startTime >= 10: # Assume failed to open on timeout
                        FDAR.stateMachine["CAMCHANGE"] = False
                        FDAR.status = "Opening camera timed out"
                        renpy.restart_interaction()
                elif FDAR.stateMachine["PREPARING"]:
                    if MASM.hasDataBool("FDAR_FAILURE"):
                        FDAR.stateMachine["PREPARING"] = False
                        FDAR.status = "Preparing failed"
                        renpy.restart_interaction()
                    elif MASM.hasDataBool("FDAR_MEMORIZE_LOWLIGHT"):
                        FDAR.stateMachine["PREPARING"] = False
                        FDAR.status = "Not enough light"
                        renpy.restart_interaction()
                    elif MASM.hasDataBool("FDAR_MEMORIZE_DONE"):
                        FDAR.stateMachine["PREPARING"] = False
                        if not FDAR.initPrepared:
                            FDAR.initPrepared = True
                            FDAR._memorizePlayer(removeOld = False, overrideTimeout = 1)
                        else:
                            FDAR.status = "Ready!"
                            renpy.restart_interaction()
                    elif MASM.hasDataBool("FDAR_NOPREPAREDATA"):
                        if not FDAR.initPrepared: # Don't update data immediately if we are already taking initial one
                            FDAR.initPrepared = True
                    elif time.time() - lastTime > 1.0:
                        FDAR.status = "Preparing, please wait{}".format(coolDots)
                        renpy.restart_interaction()
                        if len(coolDots) < 3:
                            coolDots += "."
                        else:
                            coolDots = "."
                        lastTime = time.time()
                    elif time.time() - startTime >= prepareTimeout: # Assume something failed on timeout
                        FDAR.stateMachine["PREPARING"] = False
                        FDAR.status = "Preparing timed out"
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

            FDAR.status = None
            FDAR.workaroundAllowState = False # TODO: Init can be used for this, replace..
            FDAR._setKeepOpen(persistent.submods_dathorse_FDAR_keepOpen)
            FDAR._setTimeout(persistent.submods_dathorse_FDAR_detectionTimeout)
            FDAR._setMemoryTimeout(persistent.submods_dathorse_FDAR_memoryTimeout)
            FDAR._setDetectionMethod(persistent.submods_dathorse_FDAR_detectionMethod)
            FDAR._setAllowAccess(persistent.submods_dathorse_FDAR_allowAccess)
            if persistent.submods_dathorse_FDAR_allowAccess:
                FDAR.stateMachine["PREPARING"] = True
                FDAR._startScreenUpdate()
        
        # Closes necessary things at exit
        # This is for internal use.
        @staticmethod
        @atexit.register
        def _atExit():
            FDAR.statusThreadEvent.set()
            FDAR.statusThread.join()

        # Request to memorize player
        # This is for internal use.
        @staticmethod
        def _memorizePlayer(removeOld = False, duringRecognize = False, overrideTimeout = 0):
            if not FDAR.stateMachine["PREPARING"] and not FDAR.stateMachine["CAMCHANGE"] and persistent.submods_dathorse_FDAR_allowAccess and MASM.isWorking():
                FDAR.status = "Memorize requested"
                if not duringRecognize:
                    FDAR.status = "Preparing, please wait"
                    renpy.restart_interaction()
                    FDAR.stateMachine["PREPARING"] = True
                    FDAR._startScreenUpdate()
                MASM.sendData("FDAR_MEMORIZE", (removeOld, overrideTimeout))

        # Sets whether webcam should stay open or not.
        # This is for internal use.
        @staticmethod
        def _setKeepOpen(keepopen):
            if not FDAR.stateMachine["PREPARING"] and not FDAR.stateMachine["CAMCHANGE"] and MASM.isWorking():
                if keepopen:
                    FDAR.status = "Opening camera, please wait"
                    renpy.restart_interaction()
                    FDAR.stateMachine["CAMCHANGE"] = True
                    FDAR._startScreenUpdate()
                MASM.sendData("FDAR_KEEPOPEN", keepopen)
                persistent.submods_dathorse_FDAR_keepOpen = keepopen

        # Switches whether webcam should stay open or not.
        # This is for internal use.
        @staticmethod
        def _switchKeepOpen():
            if not FDAR.stateMachine["PREPARING"] and not FDAR.stateMachine["CAMCHANGE"] and MASM.isWorking():
                if not persistent.submods_dathorse_FDAR_keepOpen:
                    persistent.submods_dathorse_FDAR_keepOpen = True
                else:
                    persistent.submods_dathorse_FDAR_keepOpen = False
                FDAR._setKeepOpen(persistent.submods_dathorse_FDAR_keepOpen)

        # Sets whether webcam access is allowed or not.
        # This is mainly for internal use. However if you wish to have dialogue where Monika changes access herself, it's fine to use this.
        @staticmethod
        def _setAllowAccess(allowed): # TODO: CHECK IF BUTTONS CAN BE PRESSED DURING BAD STATES
            if not FDAR.stateMachine["PREPARING"] and MASM.isWorking():
                if allowed and not FDAR.workaroundAllowState:
                    MASM.sendData("FDAR_ALLOWACCESS", allowed)
                    FDAR.status = "Access allowed"
                    FDAR.workaroundAllowState = True
                    FDAR.stateMachine["PREPARING"] = True
                elif not allowed:
                    MASM.sendData("FDAR_ALLOWACCESS", allowed)
                    FDAR.status = "Access not allowed"
                    FDAR.workaroundAllowState = False
                persistent.submods_dathorse_FDAR_allowAccess = allowed

        # Switches whether webcam access is allowed or not.
        # This is for internal use.
        @staticmethod
        def _switchAllowAccess():
            if not FDAR.stateMachine["PREPARING"] and not FDAR.stateMachine["CAMCHANGE"] and MASM.isWorking():
                if not persistent.submods_dathorse_FDAR_allowAccess:
                    persistent.submods_dathorse_FDAR_allowAccess = True
                else:
                    persistent.submods_dathorse_FDAR_allowAccess = False
                FDAR._setAllowAccess(persistent.submods_dathorse_FDAR_allowAccess)

        # Sets timeout.
        # This is for internal use.
        @staticmethod
        def _setTimeout(timeout):
            if not FDAR.stateMachine["PREPARING"] and not FDAR.stateMachine["CAMCHANGE"] and MASM.isWorking():
                MASM.sendData("FDAR_SETTIMEOUT", timeout)
                persistent.submods_dathorse_FDAR_detectionTimeout = timeout

        # Switches timeout.
        # This is for internal use
        @staticmethod
        def _switchTimeout():
            if not FDAR.stateMachine["PREPARING"] and not FDAR.stateMachine["CAMCHANGE"] and MASM.isWorking():
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
            if not FDAR.stateMachine["PREPARING"] and not FDAR.stateMachine["CAMCHANGE"] and MASM.isWorking():
                MASM.sendData("FDAR_SETMEMORYTIMEOUT", timeout)
                persistent.submods_dathorse_FDAR_memoryTimeout = timeout

        # Switches memory timeout
        # This is for internal use
        @staticmethod
        def _switchMemoryTimeout():
            if not FDAR.stateMachine["PREPARING"] and not FDAR.stateMachine["CAMCHANGE"] and MASM.isWorking():
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
            if not FDAR.stateMachine["PREPARING"] and not FDAR.stateMachine["CAMCHANGE"] and MASM.isWorking():
                MASM.sendData("FDAR_DETECTIONMETHOD", method)
                persistent.submods_dathorse_FDAR_detectionMethod = method

        # Switches detection, for internal use
        @staticmethod
        def _switchDetectionMethod():
            if not FDAR.stateMachine["PREPARING"] and not FDAR.stateMachine["CAMCHANGE"] and MASM.isWorking():
                if persistent.submods_dathorse_FDAR_detectionMethod == "HAAR":
                    persistent.submods_dathorse_FDAR_detectionMethod = "DNN"
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
            if not FDAR.stateMachine["PREPARING"] and not FDAR.stateMachine["CAMCHANGE"] and persistent.submods_dathorse_FDAR_allowAccess and MASM.isWorking():
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
        @staticmethod
        def canSee(person = "Player"):
            if FDAR.canRecognize():
                if not FDAR.stateMachine["RECOGNIZING"] and not FDAR.stateMachine["MEMORIZING"]:
                    if not FDAR.keepOpenTimedOutOnce:
                        MASM.sendData("FDAR_RECOGNIZEONCE", person)
                    FDAR.stateMachine["RECOGNIZING"] = True
                    FDAR.timeoutTime = time.time()
                    FDAR.extraTimeOnce = False
                    FDAR.timedOutOnce = False
                    FDAR.lightTime = None

                while time.time() - FDAR.timeoutTime < persistent.submods_dathorse_FDAR_detectionTimeout and MASM.isWorking():
                    if FDAR.stateMachine["MEMORIZING"]:
                        if MASM.hasDataBool("FDAR_MEMORIZE_DONE"):
                            FDAR.stateMachine["MEMORIZING"] = False
                            return -2
                        elif MASM.hasDataBool("FDAR_MEMORIZE_LOWLIGHT") and FDAR.lightTime is None:
                            FDAR._memorizePlayer(duringRecognize = True) # Keep trying
                            FDAR.lightTime = time.time()
                            return -1
                        elif FDAR.lightTime is not None and time.time() - FDAR.lightTime > 3: # Return back to "this might take a while" if lights are good now
                            FDAR.lightTime = None
                            return -2
                    elif FDAR.stateMachine["RECOGNIZING"]:
                        if MASM.hasDataBool("FDAR_NOTMEMORIZED"):
                            FDAR.stateMachine["MEMORIZING"] = True
                            FDAR.stateMachine["RECOGNIZING"] = False
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
                            FDAR.stateMachine["RECOGNIZING"] = False
                            FDAR.stateMachine["MEMORIZING"] = False
                            FDAR.keepOpenTimedOutOnce = False
                            FDAR.timedOutOnce = False
                            return 0
                        elif MASM.hasDataValue("FDAR_RECOGNIZED") == person:
                            MASM.hasDataBool("FDAR_RECOGNIZED") # And here..
                            FDAR.stateMachine["RECOGNIZING"] = False
                            FDAR.stateMachine["MEMORIZING"] = False
                            FDAR.keepOpenTimedOutOnce = False
                            FDAR.timedOutOnce = False
                            return 1

                    time.sleep(0.1) # Just to ease up on the loop

                FDAR.stateMachine["RECOGNIZING"] = False
                FDAR.stateMachine["MEMORIZING"] = False
                if not FDAR.timedOutOnce and MASM.isWorking():
                    if not persistent.submods_dathorse_FDAR_keepOpen and not FDAR.keepOpenTimedOutOnce:
                        FDAR.keepOpenTimedOutOnce = True # Webcam opening can take time # TODO: Check when open?
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
    vbox:
        box_wrap False
        xfill True
        xmaximum 1000
        style_prefix "check"

        text "FDAR Status: [statusStr]"

        if _tooltip:
            textbutton _("Allow webcam access: {}".format(persistent.submods_dathorse_FDAR_allowAccess)):
                action Function(FDAR._switchAllowAccess)
                hovered SetField(_tooltip, "value", "Toggle whether to allow access to your webcam.")
                unhovered SetField(_tooltip, "value", _tooltip.default)
        else:
            textbutton _("Allow webcam access: {}".format(persistent.submods_dathorse_FDAR_allowAccess)):
                action Function(FDAR._switchAllowAccess)

        if _tooltip:
            textbutton _("Keep webcam open: {}".format(persistent.submods_dathorse_FDAR_keepOpen)):
                action Function(FDAR._switchKeepOpen)
                hovered SetField(_tooltip, "value", "Toggle whether webcam should stay open even if recognition is not happening. Keep this on if your webcam opens slowly.")
                unhovered SetField(_tooltip, "value", _tooltip.default)
        else:
            textbutton _("Keep webcam open: {}".format(persistent.submods_dathorse_FDAR_keepOpen)):
                action Function(FDAR._switchKeepOpen)
                
        if _tooltip:
            textbutton _("Detection method: {}".format(persistent.submods_dathorse_FDAR_detectionMethod)):
                action Function(FDAR._switchDetectionMethod)
                hovered SetField(_tooltip, "value", "HAAR is faster and better with low-light, but is less accurate. DNN is slower and bad with low-light, but is more accurate.")
                unhovered SetField(_tooltip, "value", _tooltip.default)
        else:
            textbutton _("Detection method: {}".format(persistent.submods_dathorse_FDAR_detectionMethod)):
                action Function(FDAR._switchDetectionMethod)

        hbox:
            if _tooltip:
                textbutton _("Recognize timeout: {}s".format(persistent.submods_dathorse_FDAR_detectionTimeout)):
                    action Function(FDAR._switchTimeout)
                    hovered SetField(_tooltip, "value", "How long will Monika try to see you for before giving up.")
                    unhovered SetField(_tooltip, "value", _tooltip.default)
            else:
                textbutton _("Recognize timeout: {}s".format(persistent.submods_dathorse_FDAR_detectionTimeout)):
                    action Function(FDAR._switchTimeout)

            if _tooltip:
                textbutton _("Memorization stop after: {}s".format(persistent.submods_dathorse_FDAR_memoryTimeout)):
                    action Function(FDAR._switchMemoryTimeout)
                    hovered SetField(_tooltip, "value", "How long will Monika memorize you for initially, longer is better but\n uses more space (limited to 60MB at 3s - 200MB at 10s)")
                    unhovered SetField(_tooltip, "value", _tooltip.default)
            else:
                textbutton _("Memorization stop after: {}s".format(persistent.submods_dathorse_FDAR_memoryTimeout)):
                    action Function(FDAR._switchMemoryTimeout)

        hbox:
            if _tooltip:
                textbutton _("Update Memory"):
                    action Function(FDAR._memorizePlayer, False, False, 1)
                    hovered SetField(_tooltip, "value", "Adds your current look to Monika's memory so she can see you easier.")
                    unhovered SetField(_tooltip, "value", _tooltip.default)
            else:
                textbutton _("Update Memory"):
                    action Function(FDAR._memorizePlayer, False, False, 1)
                
            if _tooltip:
                textbutton _("Re-Memorize"):
                    action Function(FDAR._memorizePlayer, True)
                    hovered SetField(_tooltip, "value", "Complete re-memorization if you have issues with Monika seeing you no matter what.")
                    unhovered SetField(_tooltip, "value", _tooltip.default)
            else:
                textbutton _("Re-Memorize"):
                    action Function(FDAR._memorizePlayer, True)
