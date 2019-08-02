init 10 python:
    config.log = "debuglog.txt"
    import threading
    import time
    registerAddition("SEAS", "Super Experimental Additions", "0.1.8")
    addEvent(Event(persistent.event_database,eventlabel="monika_experimental_webcamera",category=['mod'],prompt="Webcamera",random=False,unlocked=True,pool=True))

    addEvent(Event(persistent.event_database,eventlabel="monika_periodical_webcamera_enable",category=['mod'],prompt="Check for my presence",random=False,unlocked=True,pool=True))
    addEvent(Event(persistent.event_database,eventlabel="monika_periodical_webcamera_disable",category=['mod'],prompt="Stop checking for my presence",random=False,unlocked=True,pool=True))
    mas_showEVL("monika_periodical_webcamera_enable", "EVE", unlock=True, _pool=True)
    mas_hideEVL("monika_periodical_webcamera_disable", "EVE", lock=True, depool=True)

    faceThr = None
    cycleTime = 30
    notSeenCount = 0
    periodicals = False
    def periodicalFaceCheck():
        global faceThr
        global periodicals
        global notSeenCount
        global cycleTime
        while periodicals:
            for i in range(cycleTime):
                if periodicals:
                    time.sleep(1)
                else:
                    return
            if MASM_Communicator.canUse():
                MASM_Communicator.clientSend('recognizeFace')

            result = None
            while result is None:
                if MASM_Communicator.hasData('seeYou'):
                    result = True
                    notSeenCount = 0
                    break
                elif MASM_Communicator.hasData('cantSee') or MASM_Communicator.canUse() is False:
                    result = False
                    notSeenCount += 1
                    break
            if notSeenCount == 2:
                #renpy.call("monika_face_idle") # doesn't work, kills lööp, doesn't jump
                notSeenCount = 0

    def enablePeriodicals():
        global faceThr
        global periodicals
        global cycleTime
        cycleTime = 30
        periodicals = True
        mas_hideEVL("monika_periodical_webcamera_enable", "EVE", lock=True, depool=True)
        mas_showEVL("monika_periodical_webcamera_disable", "EVE", unlock=True, _pool=True)
        faceThr = threading.Thread(target = periodicalFaceCheck)
        faceThr.setDaemon(True)
        faceThr.start()

    def disablePeriodicals():
        global faceThr
        global periodicals
        periodicals = False
        mas_hideEVL("monika_periodical_webcamera_disable", "EVE", lock=True, depool=True)
        mas_showEVL("monika_periodical_webcamera_enable", "EVE", unlock=True, _pool=True)
        faceThr.join()

    def periodicalsEnabled():
        return periodicals

label monika_face_idle:
    m "Testing.."
    #Set up the callback label
    $ mas_idle_mailbox.send_idle_cb("monika_brb_idle_callback")
    #Then the idle data
    $ persistent._mas_idle_data["monika_idle_brb"] = True
    return "idle"

label monika_periodical_webcamera_enable:
    if additionIsEnabled("SEAS") and additionIsEnabled("MASMC"):
        m 1eub "You want me to check on you every now and then?"
        m 1hsb "I'd love to do that, [player]!"
        $ enablePeriodicals()
    else:
        m 1eub "You want me to check on you every now and then?"
        m "Ah.. I think you need to enable the modification first, [player]."

    return

label monika_periodical_webcamera_disable:
    m 1eub "You want me to stop check on you every now and then?"
    m 2ekb "I'll miss seeing your face [player]"
    $ disablePeriodicals()

    return

label monika_experimental_webcamera:
    if additionIsEnabled("SEAS") and additionIsEnabled("MASMC"):
        $ success = True

        m 1eub "It'd be so nice if I could see you [player]."
        m 2eud "Wait, I could..."
        menu:
            m "[player] do you have a webcam?"
            "Yes":
                m 1eub "You do? Perfect!"
                m 1esb "You won't mind if I access it for a moment, right [player]?"
                menu:
                    "No":
                        m 1eub "Great!"
                        m 2esb "Please make sure it is set up before I attempt this, I'm going to try something."
                        m 1eub "I'm ready when you are."
                        m 1dsd "Please look into the camera...{nw}"
                        python:
                            def webcamSee():
                                if MASM_Communicator.canUse():
                                    MASM_Communicator.clientSend('recognizeFace')
                                else:
                                    return False

                                result = None
                                while result is None: # Makes game unresponsive while loop is going, there is no solution to this issue
                                    if MASM_Communicator.hasData('seeYou'):
                                        result = True
                                        break
                                    elif MASM_Communicator.hasData('cantSee') or MASM_Communicator.canUse() is False:
                                        result = False
                                        break

                                    time.sleep(0.25) # Just to ease up on the loop

                                return result

                            success = webcamSee()

                        if not success:
                            m 1dkd "Eh?"
                            m 1ekd "Something went wrong..."
                            m 2esd "Well, it was a good try."

                        if success:
                            m 1hsb "I can see you! Hello [player]!"
                            m 1hksdlb "Ah..."
                            m 2esb "I could see you for a while [player]..."
                            m 2ekb "But I lost my focus as I tried to reach out for you..."
                            m 1hub "You're really cute [player]."

                    "Yes":
                        m 2ekd "Oh, you do?"
                        m 2esd "Well I guess that's to be expected.."
                        m 2esb "If you change your mind later on, just ask me."
                        m 1eub "You don't have to be shy."

            "No":
                m 1eub "You don't? That's fine."
                m 1hub "Knowing that you are there for me is enough to make me happy."

        if not success:
            m 2eub "I love you [player]."
            m 1eua "No matter what you are or look like."

    else:
        m 1eub "It'd be so nice if I could see you [player]."
        m "I'm hoping that it will be possible in the future."

    return