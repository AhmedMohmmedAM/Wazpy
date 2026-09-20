import subprocess, socket, queue, threading, json, time, os, shelve, dbm.dumb
from concurrent.futures import ThreadPoolExecutor
from .utils.message import Message
from .utils.connection import Connection
from .utils.command import Command
from .utils.qrcode import QRCode
from .utils.reaction import Reaction

_SERVER_JS_PATH = os.path.join(os.path.dirname(__file__), "node", "server.js")
_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "node", "config.json")

with open(_CONFIG_PATH, "r", encoding="utf-8") as file:
    config = json.load(file)

class NodeJS:
    def __init__(self, port: int, host: str, saveCache: bool, cacheFileName: str, dataDir: str):
        self.port = port
        self.host = host
        self.configPath = _CONFIG_PATH
        self.config = config

        if config["serverPort"] != port:
            config["serverPort"] = port
            with open(_CONFIG_PATH, "w", encoding="utf-8") as file:
                json.dump(config, file, indent=4, ensure_ascii=False)

        if config["serverHost"] != host:
            config["serverHost"] = host
            with open(_CONFIG_PATH, "w", encoding="utf-8") as file:
                json.dump(config, file, indent=4, ensure_ascii=False)

        kwargs = {}
        if os.name == "posix":
            kwargs["start_new_session"] = True
        elif os.name == "nt":
            kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP

        self.process = subprocess.Popen(
            ["node", _SERVER_JS_PATH],
            **kwargs
        )

        # atexit.register(self.end)

        self.sock = socket.socket()
        self.connectToServer()

        self.responses = queue.Queue()

        self.events = {}
        self.event_clss = {
            "message": Message,
            "command": Command,
            "login": QRCode,
            "connection": Connection,
            "reaction": Reaction,
        }

        os.makedirs(dataDir, exist_ok=True)
        if saveCache:
            cachePath = os.path.join(dataDir, cacheFileName)
            db = dbm.dumb.open(cachePath, "c")
            self.messageCache = shelve.Shelf(db, writeback=False)
        else:
            self.messageCache = {}

        self.lastMessage = None
        self.ended = False

        self.executor = ThreadPoolExecutor(max_workers=10)

        self.threading = threading.Thread(
            target=self.receive,
            daemon=True
        )
        self.threading.start()

    def connectToServer(self):
        for _ in range(50):
            try:
                self.sock.connect((self.host, self.port))
                return
            except ConnectionRefusedError:
                time.sleep(0.1)

        raise ConnectionError("Could not connect to Node.js server")

    def runCallBack(self, callback, message):
        try:
            callback(message)
        except Exception:
            import traceback
            traceback.print_exc()

    def receive(self):
        buffer = ""

        try:
            while True:
                data = self.sock.recv(4096)

                if not data:
                    break

                buffer += data.decode("utf-8")

                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)

                    if not line:
                        continue

                    try:
                        message = json.loads(line)
                    except json.JSONDecodeError:
                        print(f"Warning: invalid JSON received: {line!r}")
                        continue

                    if message.get("type") == "event":
                        event = message.get("event")
                        callback = self.events.get(event)
                        cls = self.event_clss.get(event)

                        instance = None
                        if cls is not None:
                            try:
                                instance = cls(message, self)
                            except Exception:
                                import traceback
                                traceback.print_exc()
                                continue

                            if event == "message":
                                self.lastMessage = instance
                            elif event == "command":
                                self.lastMessage = instance.msg
                        elif callback:
                            print(f"Warning: no class is defined for '{event}'")
                            instance = message

                        if callback and instance is not None:
                            self.executor.submit(self.runCallBack, callback, instance)
                    else:
                        self.responses.put(message)
        except OSError:
            if not self.ended:
                import traceback
                traceback.print_exc()

    def on(self, event, callback):
        self.events[event] = callback

    def send(self, message):
        data = json.dumps(message).encode("utf-8") + b"\n"
        self.sock.sendall(data)
        try:
            return self.responses.get()
        except queue.Empty:
            print(f"[\033[1;32mWazpy-Client\033[0m] No response for action: {message.get("action")}")
            return {"success": False, "message": "timeout"}

    def end(self):
        if self.ended:
            return

        self.ended = True

        if hasattr(self.messageCache, "close"):
            self.messageCache.close()

        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass

        try:
            self.sock.close()
        except OSError:
            pass

        if self.threading.is_alive():
            self.threading.join(timeout=1)

        if self.process.poll() is None:
            self.process.terminate()

            try:
                self.process.wait()
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()