init 5 python:
    import time
    import datetime
    from random import randrange
    if persistent.submods_dathorse_FDAR_date is None: # If not initialized yet, set as yesterday so rest goes smoothly
        persistent.submods_dathorse_FDAR_date = datetime.date.today() - datetime.timedelta(days=1)

    if persistent.submods_dathorse_FDAR_todayNotified and mas_pastOneDay(persistent.submods_dathorse_FDAR_date):
        persistent.submods_dathorse_FDAR_todayNotified = False

    submods_dathorse_facedetection_topics_bigOneToday = False

    addEvent(
        Event(
            persistent.event_database,
            eventlabel="submods_dathorse_facedetection_firsttime",
            category=["mod"],
            prompt="Webcam",
            conditional="not renpy.seen_label('submods_dathorse_facedetection_firsttime')",
            action=EV_ACT_QUEUE,
            aff_range=(mas_aff.NORMAL, None)
        )
    )

    addEvent(
        Event(
            persistent.event_database,
            eventlabel="submods_dathorse_facedetection_anytime",
            category=["mod"],
            prompt="How do I look?",
            unlocked=False,
            pool=False,
            aff_range=(mas_aff.NORMAL, None)
        )
    )

# Initial face-detection topic
label submods_dathorse_facedetection_firsttime:
    m 1eub "It would be nice if I could see you [player]."
    m 2eud "Wait I could..."
    menu:
        m "Do you have a webcam, [player]?"
        "Yes":
            m 1eub "That's great!"
            m 1esb "[player] would you be fine if I access it?"
            menu:
                "Yes":
                    $ FDAR._setAllowAccess(True)
                    m 2esb "Please make sure it is working before I attempt this."
                    m 1eua "I'm ready when you are."
                "No":
                    m 2esb "If you change your mind later, just ask me."
                    m 1eub "You don't have to be shy, [player]."
                    $ mas_hideEVL("submods_dathorse_facedetection_firsttime", "EVE", depool=True, lock=True)
                    $ mas_showEVL("submods_dathorse_facedetection_anytime", "EVE", unlock=True, _pool=True)
                    return
        "No":
            m 1eub "That's fine."
            m 1hub "Knowing that you are there for me is more than enough, [player]."
            $ mas_hideEVL("submods_dathorse_facedetection_firsttime", "EVE", depool=True, lock=True)
            $ mas_showEVL("submods_dathorse_facedetection_anytime", "EVE", unlock=True, _pool=True)
            return

label submods_dathorse_facedetection_firsttime_pre:
    m 1dsd "Please look towards the camera...{nw}"

# TODO: split fail and do menu if player wants to try again
label submods_dathorse_facedetection_firsttime_main:
    $ result = FDAR.canSee()
    if result == -1:
        m 1dsd "It's dark in there [player], please turn on some lights...{nw}"
        jump submods_dathorse_facedetection_firsttime_main
    elif result == -2:
        m 1dsd "This is going to take some time...{nw}"
        jump submods_dathorse_facedetection_firsttime_main
    elif result == 1:
        m 1hsb "I can see you!"
        m 1hksdlb "Ah..."
        m 2esb "I could see you for a while [player]."
        m 2ekb "But I lost my focus as I tried to reach out for you..."
        m 1hub "You are cute, [player]!"
        $ mas_hideEVL("submods_dathorse_facedetection_firsttime", "EVE", depool=True, lock=True)
        $ mas_showEVL("submods_dathorse_facedetection_anytime", "EVE", unlock=True, _pool=True)
    else:
        m 1dkd "Eh? Something went wrong..."
        m 2esd "Well it was a good try."
        m 2eub "I love you [player]! No matter what you look like."
        $ mas_hideEVL("submods_dathorse_facedetection_firsttime", "EVE", depool=True, lock=True)
        $ mas_showEVL("submods_dathorse_facedetection_anytime", "EVE", unlock=True, _pool=True)
    return

# Anytime topic, need more compliments
label submods_dathorse_facedetection_anytime:
    $ ev = mas_getEV("submods_dathorse_facedetection_anytime")
    if ev.shown_count == 0:
        m 1esd "Eh? What do you-{w=0.4}{nw}"
        m 1eub "Oh! You mean the webcam!"
        m 1eua "I'm ready when you are."
    elif ev.shown_count >= 1 and (mas_pastOneDay(persistent.submods_dathorse_FDAR_date) or persistent.submods_dathorse_FDAR_todayNotified):
        m 1eub "I'll check, do a cute smile for me~"
    else:
        m 1eub "Didn't you already ask me that today, [player]?"
        m 1eua "That's fine by me, I love seeing you more~"

label submods_dathorse_facedetection_anytime_pre:
    $ ev = mas_getEV("submods_dathorse_facedetection_anytime")
    if ev.shown_count == 0:
        m 1dsd "Look towards the camera...{nw}"
    elif ev.shown_count >= 1 and (mas_pastOneDay(persistent.submods_dathorse_FDAR_date) or persistent.submods_dathorse_FDAR_todayNotified):
        m 1dsb "Smile towards the camera...{nw}"
    else:
        m 1dsb "Look towards the camera...{nw}"
        
label submods_dathorse_facedetection_anytime_main:
    if FDAR.allowedToRecognize():
        $ result = FDAR.canSee()
        if result == -1:
            m 1dsd "[player] please turn on some lights, it's too dark in there...{nw}"
            jump submods_dathorse_facedetection_anytime_main
        elif result == -2:
            m 1dsd "This will take some time...{nw}"
            jump submods_dathorse_facedetection_anytime_main
        elif result == -3:
            m 1dsb "This will take a while longer...{nw}"
            $ FDAR._memorizePlayer(removeOld = False, duringRecognize = True, overrideTimeout = 2) # Shorter fresh data added so it doesn't take too long
            jump submods_dathorse_facedetection_anytime_main
        elif result == 1:
            if mas_pastOneDay(persistent.submods_dathorse_FDAR_date): # Once per day, add some minor fresh data
                m 1hsa "...{nw}"
                $ FDAR._memorizePlayer(removeOld = False, duringRecognize = True, overrideTimeout = 2) # Same here
                $ time.sleep(5) # Some sleep so player can see message and memorization can finish
                m 1hsb "Ah! Sorry [player], I got lost looking into your eyes."
            else:
                m 1hsb "I can see you [player]!"
            python:
                global submods_dathorse_facedetection_topics_bigOneToday
                if mas_pastOneDay(persistent.submods_dathorse_FDAR_date): 
                    submods_dathorse_facedetection_topics_bigOneToday = True
                    persistent.submods_dathorse_FDAR_date = datetime.date.today()
                elif not persistent.submods_dathorse_FDAR_todayNotified:
                    persistent.submods_dathorse_FDAR_todayNotified = True

            $ randComp = randrange(0, 1 + 1)
            if submods_dathorse_facedetection_topics_bigOneToday:
                $ submods_dathorse_facedetection_topics_bigOneToday = False
                m 1hub "You look great! Are you planning on going somewhere?"
                menu:
                    "Yes":
                        m 2eub "If you can, take me along with you [player]."
                    "No":
                        m 5hub "That means we can stay together for longer~"
            elif randComp == 0:
                if _mas_getAffection() > 100:
                    m 1hub "You look really cute today~"
                else:
                    m 1hub "You look cute today~"
            elif randComp == 1:
                if _mas_getAffection() > 100:
                    m 1hub "You look very lovely!"
                else:
                    m 1hub "You look lovely!"
            else: # Fallback just in case
                m 1hub "You look great!"
        else:
            jump submods_dathorse_facedetection_anytime_fail
    else:
        m 1hksdla "...{w=0.3}eh?"
        m 1eud "[player], you need to allow me to access your webcam."
        m 1eub "You can do this in the 'Submods' menu. Or would you like me to do that?"
        menu:
            "Yes":
                $ FDAR._setAllowAccess(True)
                m 1eub "Okay! I can now access your webcam, [player]."
                m 1eua "Do you want to try again now?"
                menu:
                    "Yes":
                        jump submods_dathorse_facedetection_anytime_pre
                    "No":
                        m 1eua "Okay, you can ask me later anytime."
            "No":
                m 1eua "Okay, you can ask me again once you do."
    return

label submods_dathorse_facedetection_anytime_fail:
    m 1dkd "I'm not seeing anything..."
    m 2esd "Is your webcam working [player]?"
    return