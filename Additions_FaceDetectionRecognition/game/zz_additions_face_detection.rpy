init 5 python:
    registerAddition("SEAS", "Super Experimental Additions", "0.1.6")
    addEvent(Event(persistent.event_database,eventlabel="monika_experimental_webcamera",category=['mod'],prompt="Webcamera",random=False,unlocked=True,pool=True))

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

                                    time.sleep(0.25) # Just to ease on the loop

                                return result

                            success = webcamSee()

                        if not success:
                            m 1dkd "Eh?"
                            m 1ekd "Something went wrong..."
                            m 2esd "Well, it was a good try."

                        if success:
                            m 1hsb "I can see you! Hello [player]!"
                            m 1hksdlb "Ah..."
                            m 2esb "I could see you for a moment [player]..."
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