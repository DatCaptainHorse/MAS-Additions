init 4 python:
    #config.log = "debuglog.txt"
    registerAddition("MASMC", "MASM Communicator", "0.1.7")
    import signal
    import socket
    import select
    import threading
    import subprocess
    import time
    import atexit

    if additionIsEnabled("MASMC"):
        # Threaded socket communicator
        class MASM_Communicator:
            data = []
            clientTCP = None
            serverTCP = None
            serverUDP = None
            masmApp = None
            appPath = None
            appExists = False
            useUDP = False

            def __init__(self):
                self.thread = None

            def connectMASM(self, UDPmode):
                MASM_Communicator.useUDP = UDPmode
                if MASM_Communicator.useUDP:
                    if MASM_Communicator.serverUDP is None:
                        MASM_Communicator.serverUDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        MASM_Communicator.serverUDP.settimeout(0.01)
                        MASM_Communicator.serverUDP.bind(("127.0.0.1", 23456))
                else:
                    if MASM_Communicator.serverTCP is None:
                        MASM_Communicator.serverTCP = socket.socket()
                        MASM_Communicator.serverTCP.settimeout(0.01)
                        MASM_Communicator.serverTCP.bind(("127.0.0.1", 12345))
                        MASM_Communicator.serverTCP.listen(5)

                    if MASM_Communicator.clientTCP is None:
                        while True:
                            try:
                                MASM_Communicator.clientTCP, addr = MASM_Communicator.serverTCP.accept()
                            except socket.error:
                                continue
                            break
                
                self.thread = threading.Thread(target = self.communicateWithClient)
                self.thread.setDaemon(True)
                self.thread.start()

            def communicateWithClient(self):
                while MASM_Communicator.appExists:
                    received = None
                    try:
                        if MASM_Communicator.useUDP:
                            received, addr = MASM_Communicator.serverUDP.recvfrom(64)
                        else:
                            rtr, rtw, err = select.select((MASM_Communicator.clientTCP,), (), (), 0)
                            if rtr:
                                received = MASM_Communicator.clientTCP.recv(64)

                    except socket.error: # No data
                        pass

                    if received is not None:
                        #renpy.log("MASMC received data: {}".format(received))
                        received = received.decode('utf-8')
                        MASM_Communicator.data.append(received)

                    if MASM_Communicator.masmApp is not None:
                        poll = MASM_Communicator.masmApp.poll()
                        if poll == None:
                            MASM_Communicator.appExists = True
                        else:
                            MASM_Communicator.appExists = False
                    
            @staticmethod
            def hasData(dat):
                if dat in MASM_Communicator.data:
                    MASM_Communicator.data.remove(dat)
                    return True
                else:
                    return False

            @staticmethod
            def canUse():
                return MASM_Communicator.appExists

            @staticmethod
            def clientSend(toSend):
                if MASM_Communicator.useUDP:
                    if MASM_Communicator.serverUDP is not None:
                        MASM_Communicator.serverUDP.sendto(toSend.encode('utf-8'), ("127.0.0.1", 34567))
                else:
                    if MASM_Communicator.clientTCP is not None:
                        MASM_Communicator.clientTCP.sendall(toSend.encode('utf-8'))

            @staticmethod
            def exiting():
                if MASM_Communicator.masmApp is not None:
                    poll = MASM_Communicator.masmApp.poll()
                    if poll == None:
                        os.kill(MASM_Communicator.masmApp.pid, signal.SIGTERM) # do it peacefully Python

            @staticmethod
            def startMASM():
                for dirpath,subdirs,files in os.walk('.'):
                    if 'MASM' in subdirs:
                        MASM_Communicator.appPath = dirpath
                        break

                if MASM_Communicator.appPath is not None:
                    if renpy.windows: # If we are running on Windows OS
                        MASM_Communicator.masmApp = subprocess.Popen(renpy.loader.transfn(os.path.join(MASM_Communicator.appPath, '/MASM/MASM.exe'))) # Open MASM application subprocess
                    elif renpy.linux or renpy.macintosh: # Linux / Mac..
                        MASM_Communicator.masmApp = subprocess.Popen(renpy.loader.transfn(os.path.join(MASM_Communicator.appPath, '/MASM/MASM'))) # Good luck!

                    if MASM_Communicator.masmApp is not None:
                        MASM_Communicator.appExists = True

                atexit.register(MASM_Communicator.exiting) # Because subprocesses
                signal.signal(signal.SIGTERM, MASM_Communicator.exiting)
                signal.signal(signal.SIGINT, MASM_Communicator.exiting)

        communicator = MASM_Communicator()
        communicator.startMASM()
        communicator.connectMASM(True)

        if isAdditionFirstRun("MASMC"):
            MASM_Communicator.clientSend("first")
        else:
            MASM_Communicator.clientSend("notFirst")