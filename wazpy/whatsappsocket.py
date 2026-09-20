import string, time, sys
from typing import Literal
from .nodejs import NodeJS
from .browser import Browser

EventsNames = Literal["message", "command", "login", "connection", "reaction", "shutdown"]

class WhatsAppSocket:
    def __init__(
            self, 
            authName: str = "auth", 
            cacheFileName: str = "cache.db",
            dataDir: str = ".wazpy",
            saveCache: bool = True,
            loggerLevel: str = "silent", 
            syncFullHistory: bool = False, 
            browserInfo: list = Browser.ubuntu("Chrome"), 
            commandPrefixs: list[str] = ["."], 
            commandCaseSens: bool = True,
            nodeJSPort: int =  "default",
            nodeJSHost: str = "default"
        ):

        if not loggerLevel.lower() in ["debug", "error", "fatal", "info", "silent", "trace", "warn"]:
            raise SyntaxError(f"Unknown logger type {loggerLevel}")
        if not isinstance(authName, str):
            raise TypeError("authName must be string")
        if not isinstance(cacheFileName, str):
            raise TypeError("cacheFileName must be string")
        if not isinstance(saveCache, bool):
            raise TypeError("saveCache must be boolean")
        if not isinstance(dataDir, str):
            raise TypeError("cacheDir must be string")
        if not isinstance(syncFullHistory, bool):
            raise TypeError("syncFullHistory must be boolean")
        if not isinstance(commandPrefixs, list):
            raise TypeError("prefixs must be list")
        if any(len(p) != 1 for p in commandPrefixs):
            raise ValueError("Each prefix symbol must be one char")
        if not all(not p.isalnum() and not p.isspace() for p in commandPrefixs):
            raise ValueError("Each prefix symbol must be special char")
        if not isinstance(commandCaseSens, bool):
            raise TypeError("commandCaseSens must be boolean")
        if not isinstance(nodeJSHost, str):
            raise TypeError("serverHost must be string")

        if nodeJSHost == "default": nodeJSHost = "127.0.0.1"
        elif nodeJSHost == "all": nodeJSHost = "0.0.0.0"

        if nodeJSPort == "default": nodeJSPort = 5000

        if not isinstance(nodeJSPort, int):
            raise TypeError("serverPort must be integer")

        if not cacheFileName.endswith(".db"):
            cacheFileName = cacheFileName.strip() + ".db"

        self.nodeJS = NodeJS(nodeJSPort, nodeJSHost, saveCache, cacheFileName, dataDir)
        self.ended = False
        self.shutdownCallBack = None
        self._shutdownMsg = None

        response = self.nodeJS.send({
            "action": "setup", 
            "loggerLevel": loggerLevel.lower(), 
            "authName": authName,
            "dataDir": dataDir,
            "browserInfo": browserInfo,
            "syncFullHistory": syncFullHistory,
            "prefixs": commandPrefixs,
            "casesens": commandCaseSens
        })

        if not response["success"]:
            raise RuntimeError(response.get("message", "Setup failed"))

    def requestPairingCode(self, phoneNumber: str, customPairingCode: str =None):
        if not customPairingCode is None:
            if not isinstance(customPairingCode, str):
                raise TypeError("customPairingCode must be a string")
            if len(customPairingCode) != 8:
                raise SyntaxError("customPairingCode must be length 8")

            allowedChars = string.ascii_uppercase + string.digits

            if any(char not in allowedChars for char in customPairingCode):
                raise SyntaxError("customPairingCode must contain uppercase letters and digits only")

            customPairingCode = customPairingCode.upper()
        
        response = self.nodeJS.send({
            "action": "requestPairCode",
            "phoneNumber": phoneNumber,
            "customPairingCode": customPairingCode
        })

        if not response["success"]:
            raise RuntimeError(response.get("message", "Failed to get pairing code"))
        
        return response["code"]

    def getConfig(self):
        return self.nodeJS.config

    def getConfigPath(self):
        return self.nodeJS.configPath

    @property
    def shutdownMsg(self):
        return self._shutdownMsg

    @shutdownMsg.setter
    def shutdownMsg(self, msg):
        if not isinstance(msg, str):
            raise TypeError("shutdownMsg must be string")

        self.nodeJS.send({
            "action": "changeShutDownMsg",
            "message": msg
        })

        self._shutdownMsg = msg

    def start(self):
        #return self.nodeJS.send({"action": "start"})
        try:
            self.nodeJS.send({"action": "start"})
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[\033[1;32mWazpy-Client\033[0m] Exiting the program...")
            try:
                self.end()
            except KeyboardInterrupt:
                print("[\033[1;32mWazpy-Client\033[0m] Force exiting...")
                sys.exit(1)

    def on(self, event: EventsNames):
        def decorator(callback):
            if event == "shutdown":
                self.shutdownCallBack = callback
                return callback
            
            self.nodeJS.on(event, callback)
            return callback
        return decorator

    def end(self):
        if self.ended:
            return
        self.ended = True

        print("[\033[1;32mWazpy-Client\033[0m] Requesting \033[1mNodeJS-Server\033[0m to send shutdownMsg")
        self.nodeJS.send({
            "action": "sendShutdownMsg"
        })

        if self.shutdownCallBack:
            print("[\033[1;32mWazpy-Client\033[0m] Calling ShutDown function\n")

            try:
                self.shutdownCallBack(self.nodeJS.lastMessage)
            except Exception:
                import traceback
                traceback.print_exc()
        
        self.nodeJS.end()