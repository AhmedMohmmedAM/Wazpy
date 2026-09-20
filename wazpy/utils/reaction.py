from .message import Message

class Reaction:
    def __init__(self, data, nodeJS):
        reactions = data.get("reaction", [])
        self.valid = bool(reactions)
        if not self.valid:
            return

        item = reactions[0]
        self.data = data

        self.emoji = item.get("reaction", {}).get("text", "")
        self.removed = self.emoji == ""

        self.sender = item.get("key", {}).get("participant") or item.get("key", {}).get("remoteJid")
        self.fromMe = item.get("key", {}).get("fromMe")

        reactedKey = item.get("reaction", {}).get("key", {})
        self.ogMsgId = reactedKey.get("id")
        self.ogMsgChat = reactedKey.get("remoteJid")
        self.ogMsgFromMe = reactedKey.get("fromMe")

        raw = nodeJS.messageCache.get(self.ogMsgId)
        print("LOOKING FOR: ", self.ogMsgId)
        print("FOUND: ", raw)
        self.msg: Message = Message({"message": {"messages": [raw]}}, nodeJS) if raw else None