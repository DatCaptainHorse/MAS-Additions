# Changelog #
# 0.1.8 -> 2.0.0
# - Better versioning
# - Using official Submod API
# - HAAR and DNN changing with recognition timeout for better user experience
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
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="submods_dathorse_facedetection_firsttime",
            category=["mod"],
            prompt="Webcamera",
            random=False,
            unlocked=True,
            pool=True
        )
    )
    #addEvent(
    #    Event(
    #        persistent.event_database,
    #        eventlabel="submods_dathorse_facedetection",
    #        category=["mod"],
    #        prompt="Can you see me",
    #        random=False,
    #        unlocked=True,
    #        pool=True
    #    )
    #)

init -990 python:
    import time
    import threading
    # Has to be global for screen input to work
    FDAR_timeout = "15"
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

label submods_dathorse_facedetection_firsttime:
    if MASM.isWorking():
        $ success = False
        m 1eub "It would be so nice if I could see you [player]."
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
                        m 1dsd "Please look into the camera...{nw}"
                        $ success = FDAR.canSeePlayer()
                        if not success:
                            m 1dkd "Eh? Something went wrong..."
                            m 2esd "Well it was a good try!"
                        elif success:
                            m 1hsb "I can see you!"
                            m 1hksdlb "Ah..."
                            m 2esb "I could see you for a while [player]."
                            m 2ekb "But I lost my focus as I tried to reach out for you..."
                            m 1hub "You are really cute [player]!"
                    "No":
                        m 2esd "Well I guess that's to be expected."
                        m 2esb "If you change your mind later, just ask me."
                        m 1eub "You don't have to be shy."
            "No":
                m 1eub "That's fine."
                m 1hub "Knowing that you are there for me is more than enough."
        if not success:
            m 2eub "I love you [player]."
            m 1eua "No matter what you look like."
    else:
        m 1eub "It would be so nice if I could see you [player]."
        m "I'm hoping that it will be possible in the future."

    return