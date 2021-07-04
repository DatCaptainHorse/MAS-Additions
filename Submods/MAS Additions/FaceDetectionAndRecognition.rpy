# Changelog #
# 0.1.8 -> 2.0.0
# - Better versioning
# - Using official Submod API
# - HAAR and DNN changing with recognition timeout for better user experience
default persistent.submods_dathorse_FDAR_date = None

init -990 python:
    store.mas_submod_utils.Submod(
        author="DatHorse",
        name="Face Detection and Recognition",
        description=(
            "Adds facial detection and recognition functionality to MAS.\n"
            "Uses OpenCV for the process. This is done through Monika After Story Module."
        ),
        version="2.0.0",
        dependencies={
            "Monika After Story Module" : (None, None)
        },
        settings_pane="FDAR_settings_pane",
        version_updates={}
    )

init 5 python:
    import datetime
    from random import randrange
    if persistent.submods_dathorse_FDAR_date is None: # If not initialized yet, set as yesterday so rest goes smoothly
        persistent.submods_dathorse_FDAR_date = datetime.date.today() - datetime.timedelta(days=1)

    addEvent(
        Event(
            persistent.event_database,
            eventlabel="submods_dathorse_facedetection_firsttime",
            category=["mod"],
            prompt="Webcam",
            random=False,
            unlocked=True,
            pool=True,
            aff_range=(mas_aff.NORMAL, None)
        )
    )

    addEvent(
        Event(
            persistent.event_database,
            eventlabel="submods_dathorse_facedetection_anytime",
            category=["mod"],
            prompt="How do I look?",
            random=False,
            unlocked=False,
            pool=False,
            aff_range=(mas_aff.NORMAL, None)
        )
    )

init -990 python:
    import time
    import threading
    FDAR_timeout = "15" # Has to be global for screen input to work
    # Face Detection and Recognition functions
    class FDAR:
        method = "DNN" # Default to DNN for better results
        # Sends a request to detect player's face, if no face data exists it will be taken first.
        # Returns boolean True or False depending if player's face was detected, or False if timeout was triggered (by default 15 seconds, user adjustable)
        @staticmethod
        def canSeePlayer():
            startTime = time.time()
            MASM.sendData("recognizeFace.{}".format(FDAR.method))
            while time.time() - startTime < int(FDAR_timeout): # timeout after which we simply fail
                if MASM.hasData("seeYou"):
                    return True
                elif MASM.hasData("cantSee"):
                    return False
                time.sleep(0.1) # Just to ease up on the loop
            return False
        
        # Switches detection between DNN and HAAR
        @staticmethod
        def switchDetectionMethod():
            if FDAR.method == "HAAR":
                FDAR.method = "DNN"
            else:
                FDAR.method = "HAAR"

screen FDAR_settings_pane():
    python:
        submods_screen = store.renpy.get_screen("submods", "screens")
        if submods_screen:
            _tooltip = submods_screen.scope.get("tooltip", None)
        else:
            _tooltip = None
    vbox:
        box_wrap False
        xfill True
        xmaximum 1000
        style_prefix "check"
        hbox:
            if _tooltip:
                textbutton _("Face detection method: {}".format(FDAR.method)):
                    action Function(FDAR.switchDetectionMethod)
                    hovered SetField(_tooltip, "value", "HAAR is faster but less accurate, DNN is slower but more accurate")
                    unhovered SetField(_tooltip, "value", _tooltip.default)
            else:
                textbutton _("Face detection method: {}".format(FDAR.method)):
                    action Function(FDAR.switchDetectionMethod)
        hbox:
            text "Detection timeout:"
            input:
                allow "0123456789" 
                length 2
                value VariableInputValue("FDAR_timeout")

# Initial face-detection topic
label submods_dathorse_facedetection_firsttime:
    m 1eub "It would be nice if I could see you [player]."
    if MASM.isWorking():
        m 2eud "Wait I could..."
        menu:
            m "[player] do you have a webcam?"
            "Yes":
                m 1eub "That's great!"
                m 1esb "[player] would you be fine if I accessed your webcam for a moment?"
                menu:
                    "Yes":
                        m 2esb "Please make sure it is working before I attempt this."
                        m 1eub "I'm ready when you are."
                        m 1dsd "Please look towards the camera...{nw}"
                        $ success = FDAR.canSeePlayer()
                        if not success:
                            m 1dkd "Eh? Something went wrong..."
                            m 2esd "Well it was a good try!"
                            m 2eub "I love you [player]."
                            m 1eua "No matter what you look like."
                            $ mas_hideEVL("submods_dathorse_facedetection_firsttime", "EVE", depool=True)
                            $ mas_showEVL("submods_dathorse_facedetection_anytime", "EVE", unlock=True, _pool=True)
                        elif success:
                            m 1hsb "I can see you!"
                            m 1hksdlb "Ah..."
                            m 2esb "I could see you for a while [player]."
                            m 2ekb "But I lost my focus as I tried to reach out for you..."
                            m 1hub "You are cute, [player]!"
                            $ mas_hideEVL("submods_dathorse_facedetection_firsttime", "EVE", depool=True)
                            $ mas_showEVL("submods_dathorse_facedetection_anytime", "EVE", unlock=True, _pool=True)
                    "No":
                        m 2esb "If you change your mind later, just ask me."
                        m 1eub "You don't have to be shy."
                        $ mas_hideEVL("submods_dathorse_facedetection_firsttime", "EVE", depool=True)
                        $ mas_showEVL("submods_dathorse_facedetection_anytime", "EVE", unlock=True, _pool=True)
            "No":
                m 1eub "That's fine."
                m 1hub "Knowing that you are there for me is more than enough."
                $ mas_hideEVL("submods_dathorse_facedetection_firsttime", "EVE", depool=True)
                $ mas_showEVL("submods_dathorse_facedetection_anytime", "EVE", unlock=True, _pool=True)
    else:
        m "I'm hoping that it will be possible in the future."
    return

# Anytime topic, need more compliments
label submods_dathorse_facedetection_anytime:
    $ ev = mas_getEV("submods_dathorse_facedetection_anytime")
    if ev.shown_count == 0:
        m 1esd "Eh? What do you-{w=0.4}{nw}"
        m 1eub "Oh! You mean the webcam!"
        m 1eua "I'm ready when you are."
        m 1dsd "Look towards the camera...{nw}"
    elif ev.shown_count >= 1 and mas_pastOneDay(persistent.submods_dathorse_FDAR_date):
        m 1eub "I'll check, do a cute smile for me~"
        m 1dsb "Smile towards the camera...{nw}"
    else:
        m 1eub "Didn't you already ask me that today, [player]?"
        m 1eua "That's fine by me, I love seeing you more~"
        m 1dsb "Look towards the camera...{nw}"
    if MASM.isWorking():
        $ success = FDAR.canSeePlayer()
        if not success:
            m 1dkd "I'm not seeing anything..."
            m 2esd "Is your webcam working [player]?"
        elif success:
            python:
                if mas_pastOneDay(persistent.submods_dathorse_FDAR_date): 
                    persistent.submods_dathorse_FDAR_date = datetime.date.today()

            m 1hsb "I can see you [player]!"
            $ randComp = randrange(0, 1 + 1)
            if randComp == 0:
                if _mas_getAffection() > 100:
                    m 1hub "You look really cute today~"
                else:
                    m 1hub "You look cute today~"
            elif randComp == 1:
                if _mas_getAffection() > 100:
                    m 1hub "You look very lovely!"
                else:
                    m 1hub "You look lovely!"
    else:
        m 1hksdlb "...{w=0.3}eh?"
        m 2esd "Sorry [player]. For some reason I cannot access your webcam."
    return