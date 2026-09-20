class Message:
    def __init__(self, data, nodeJS):
        messages = data.get("message", {}).get("messages", [])

        self.valid = bool(messages)

        if not self.valid:
            return

        message = messages[0]

        self.data = message
        self.nodeJS = nodeJS

        self.key = message.get("key", {})
        self.id = self.key.get("id")
        self.fromMe = self.key.get("fromMe")
        self.timestamp = message.get("messageTimestamp")
        self.name = message.get("pushName")

        self.chat = self.key.get("remoteJid")
        self.chatAlt = self.key.get("remoteJidAlt")
        
        self.sender = self.key.get("participant") or self.chat
        self.senderAlt = self.key.get("participantAlt") or self.chatAlt
        self.senderNumber = self._extract_number(self.sender, self.senderAlt)

        content = message.get("message", {}) or {}

        self.text = (
            content.get("conversation")
            or content.get("extendedTextMessage", {}).get("text")
        )

        self.quoted = None
        self.quotedText = None
        self.quotedId = None
        self.quotedSender = None
        self.quotedFromMe = None
        self.quotedKey = None

        contextInfo = self._find_context_info(content)

        if contextInfo and contextInfo.get("quotedMessage"):
            self.quoted = contextInfo["quotedMessage"]
            self.quotedId = contextInfo.get("stanzaId")
            self.quotedSender = contextInfo.get("participant")
            own_jid = getattr(nodeJS, "own_jid", None)
            self.quotedFromMe = (
                (self.quotedSender == own_jid) if own_jid else None
            )
            self.quotedKey = {
                "remoteJid": self.chat,
                "fromMe": self.quotedFromMe,
                "id": self.quotedId,
                "participant": self.quotedSender,
            }

            self.quotedText = (
                self.quoted.get("conversation")
                or self.quoted.get("extendedTextMessage", {}).get("text")
            )

        if self.valid and self.id:
            try:
                nodeJS.messageCache[self.id] = self.data
                print("CACHED: ", self.id)
            except Exception:
                import traceback
                traceback.print_exc(    )

    @staticmethod
    def _extract_number(primary, alt):
        if primary and "@s.whatsapp.net" in primary:
            return primary
        if alt and "@s.whatsapp.net" in alt:
            return alt
        return primary

    @staticmethod
    def _find_context_info(content):
        for value in content.values():
            if isinstance(value, dict) and "contextInfo" in value:
                return value["contextInfo"]
        return None

    @property
    def phone(self):
        jid = self.senderNumber or self.sender or self.chat

        if jid is None or "@lid" in jid:
            return None

        return jid.split("@")[0]

    def reply(self, msg, chat=None, quoted=None):
        if not self.valid:
            return

        if chat is None:
            chat = self.chat
        if quoted is None:
            quoted = self.data
        if msg is None:
            msg = ""

        response = self.nodeJS.send({
            "action": "replyMessage",
            "chat": chat,
            "msg": str(msg),
            "quoted": quoted,
        })

        if not response["success"]:
            raise RuntimeError(response["message"])

    def send(self, msg, chat=None):
        if not self.valid:
            return

        if chat is None:
            chat = self.chat
        if msg is None:
            msg = ""

        response = self.nodeJS.send({
            "action": "sendMessage",
            "chat": chat,
            "msg": str(msg),
        })

        if not response["success"]:
            raise RuntimeError(response["message"])

    def delete(self, key=None):
        if not self.valid:
            return

        response = self.nodeJS.send({
            "action": "deleteMessage",
            "chat": self.chat,
            "key": key or self.key,
        })

        if not response["success"]:
            raise RuntimeError(response["message"])

    @staticmethod
    def isMessage(msg: Message):
        if msg is None or not msg.valid: return False
        return True