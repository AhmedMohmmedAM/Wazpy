from .message import Message

class Command:
    def __init__(self, data, nodeJS):
        self.msg = Message(data, nodeJS)

        self.name = data["command"]["name"]
        self.args = data["command"]["args"]