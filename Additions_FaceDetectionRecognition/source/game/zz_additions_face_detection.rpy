init 5 python:
    registerAddition("SEAS", "Super Experimental Additions", "0.1.5")
    addEvent(Event(persistent.event_database,eventlabel="monika_experimental_webcamera",category=['mod'],prompt="Webcamera",random=False,unlocked=True,pool=True))

label monika_experimental_webcamera:
    if additionIsEnabled("SEAS") and additionIsEnabled("MASMC"):
        $ success = False

        m 1b "It'd be so nice if I could see you [player]."
        m 1i "Wait, I could..."
        menu:
            m "[player] do you have a webcam?"
            "Yes":
                m 1b "You do? Perfect!"
                m 1a "You won't mind if I access it for a moment, right [player]?"
                menu:
                    "No":
                        m 1b "Great!"
                        m 1 "Please make sure it is set up before I attempt this, I'm going to try something experimental."
                        m 1j "I'm ready when you are."
                        m 1j "Please look into the camera...{nw}"
                        python:
                            def webcamSee():
                                MASM_DataCommunicator.clientSend("recognizeFace")

                                seenYet = False
                                while not seenYet: # Makes game unresponsive while loop is going
                                    if 'seeYou' in MASM_DataCommunicator.data:
                                        return True
                                        break
                                    elif 'cantSee' in MASM_DataCommunicator.data:
                                        return False
                                        break

                                    time.sleep(0.15) # Just to ease on the loop

                            success = webcamSee()

                        if not success:
                            m 1l "Eh? Something went wrong..."
                            m 2e "Well, it was a good try."

                        if success:
                            m 3k "I can see you! Hello [player]!"
                            m 3l "Ah..."
                            m 1b "I could see you for a moment [player]..."
                            m 1l "I lost my focus as I tried to reach out for you, ahaha..."
                            m 1k "You're really cute."

                    "Yes":
                        m 1l "Oh, you do?"
                        m 1n "Well I guess that's to be expected.."
                        m 1b "If you change your mind later on, just ask me."

            "No":
                m 1b "You don't? That's fine."
                m 1k "Knowing that you are there for me is enough to make me happy."

        if not success:
            m 1a "I love you [player], no matter what you are or look like."

    return