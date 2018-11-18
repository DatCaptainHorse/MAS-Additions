init 4 python:
    registerAddition("MASMC", "MASM Communicator", "0.1.0")
    import signal
    import socket
    import threading
    import subprocess
    import time
    import atexit

    if additionIsEnabled("MASMC"):
        # Threaded socket communicator
        class MASM_DataCommunicator:
            data = []
            client = None
            callbacks = []

            def __init__(self):
                self.server = socket.socket()
                self.port = 12345
                self.host = socket.gethostname()
                self.server.settimeout(15)
                self.server.bind((self.host, self.port))
                self.clientAddr = None

            def getClient(self):
                self.server.listen(5)
                try:
                    MASM_DataCommunicator.client, self.clientAddr = self.server.accept()
                except:
                    return
                MASM_DataCommunicator.client.setblocking(0)
                MASM_DataCommunicator.client.settimeout(5)

                thr = threading.Thread(target = self.communicateWithClient)
                thr.setDaemon(True)
                thr.start()

            def communicateWithClient(self):
                while True:
                    try:
                        received = MASM_DataCommunicator.client.recv(64).decode('utf-8')
                        if received is not None:
                            MASM_DataCommunicator.data.append(received)
                    except:
                        pass

                    if len(MASM_DataCommunicator.callbacks) > 0:
                        for dat in MASM_DataCommunicator.data:
                            for cb in MASM_DataCommunicator.callbacks:
                                cb(dat)

            @staticmethod
            def clientSend(toSend):
                if MASM_DataCommunicator.client is not None and toSend is not None:
                    MASM_DataCommunicator.client.sendall(toSend)

            @staticmethod
            def addCallback(callbackFunction):
                MASM_DataCommunicator.callbacks.append(callbackFunction)

            @staticmethod
            def removeCallback(callbackFunction):
                MASM_DataCommunicator.callbackFunction.remove(callbackFunction)

        enginePath = None
        for dirpath,subdirs,files in os.walk('.'):
            if 'MASM' in subdirs:
                enginePath = dirpath
                break

        engine = None
        def exiting():
            if engine is not None:
                poll = engine.poll()
                if poll == None:
                    os.kill(engine.pid, signal.SIGTERM) # do it peacefully Python

        atexit.register(exiting) # Because subprocesses

        communicator = None
        if enginePath:
            if renpy.windows: # If we are running on Windows OS
                try:
                    engine = subprocess.Popen(renpy.loader.transfn(os.path.join(enginePath, '/MASM/MASM.exe'))) # Open engine subprocess
                except:
                    pass
            elif renpy.linux or renpy.macintosh: # Linux / Mac..
                try:
                    engine = subprocess.Popen(renpy.loader.transfn(os.path.join(enginePath, '/MASM/MASM.sh'))) # Good luck!
                except:
                    pass

            communicator = MASM_DataCommunicator()
            communicator.getClient()

            if isAdditionFirstRun("MASMC"):
                communicator.client.sendall("first".encode('utf-8'))
            else:
                communicator.client.sendall("notFirst".encode('utf-8'))