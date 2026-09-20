# Wazpy

**Wazpy** is a Python library for building WhatsApp bots with a clean, event-driven API powered by [Baileys](https://github.com/WhiskeySockets/Baileys) under the hood. It gives you full control over messages, commands, reactions, and connection events — with an easy-to-use decorator-based syntax and built-in customization options.

Wazpy runs a lightweight Node.js server internally (bundled with the package) that talks to WhatsApp via Baileys, while you write all your bot logic in plain Python.

---

## Features

- 🎯 **Event-driven API** — simple `@bot.on(...)` decorators for every event
- 💬 **Command system** — built-in prefix-based command parsing (e.g. `.echo`, `.help`)
- 😀 **Reaction handling** — detect when users react to messages, with automatic lookup of the original message
- 🔐 **Pairing code & QR login** — connect without scanning a QR code if you prefer
- 🗂️ **Persistent message cache** — reactions can resolve the original message even after a restart
- 👋 **Graceful shutdown** — send a custom "goodbye" message when your bot shuts down
- ⚙️ **Highly configurable** — logger level, auth folder, browser identity, command case-sensitivity, and more

---

## Installation

```bash
pip install wazpy
```

> Requires [Node.js](https://nodejs.org/) to be installed on your system, since Wazpy runs a small Node.js server internally to communicate with WhatsApp.

---

## Quick Start

```python
from wazpy import WhatsAppSocket, Browser
from wazpy.utils import Message, Command, Connection, Reaction

bot = WhatsAppSocket(
    authName="auth",
    loggerLevel="silent",
    syncFullHistory=False,
    browserInfo=Browser.ubuntu("Chrome"),
    commandPrefixs=["."],
    commandCaseSens=False,
    nodeJSPort=5000,
    nodeJSHost="default",
)

def main():

    @bot.on("login")
    def onLogin(_):
        code = bot.requestPairingCode("201234567890")
        print(f"Your pairing code is: {code}")

    @bot.on("connection")
    def onConnection(conn: Connection):
        if conn.connected:
            print("Connected!")
        else:
            print(f"Disconnected ({conn.reason})")

    @bot.on("message")
    def onMessage(msg: Message):
        if not Message.isMessage(msg) or msg.fromMe:
            return

        if msg.text and "hello" in msg.text.lower():
            msg.reply("Hello there!")

    @bot.on("command")
    def onCommand(cmd: Command):
        if cmd.name == "echo":
            cmd.msg.reply(" ".join(cmd.args))

    @bot.on("reaction")
    def onReaction(react: Reaction):
        if not Message.isMessage(react.msg) or not react.msg.fromMe:
            return
        if react.removed:
            return

        if react.emoji == "🗑️":
            react.msg.delete()

    @bot.on("shutdown")
    def onShutDown(lastMsg: Message):
        if lastMsg is None or not lastMsg.valid:
            return
        lastMsg.send("Bot is shutting down. Goodbye!")

    bot.start()

if __name__ == "__main__":
    main()
```

Run it, scan the QR code (or use the pairing code), and your bot is live.

---

## Configuration Options

`WhatsAppSocket(...)` accepts the following parameters:

| Parameter | Type | Default | Description |
|---|---|---|---|
| `authName` | `str` | `"auth"` | Folder name where session credentials are stored |
| `loggerLevel` | `str` | `"silent"` | Baileys logger level (`debug`, `error`, `fatal`, `info`, `silent`, `trace`, `warn`) |
| `syncFullHistory` | `bool` | `False` | Whether to sync full chat history on connect |
| `browserInfo` | `list` | `Browser.ubuntu("Chrome")` | Browser identity shown to WhatsApp |
| `commandPrefixs` | `list[str]` | `["."]` | List of single special-character prefixes that trigger the `command` event |
| `commandCaseSens` | `bool` | `True` | Whether command names are case-sensitive |
| `nodeJSPort` | `int` | `5000` | Port used for the internal Python ↔ Node.js connection |
| `nodeJSHost` | `str` | `"default"` | Host for the internal connection (`"default"` = `127.0.0.1`, `"all"` = `0.0.0.0`) |

---

## Events Reference

Register any event with the `@bot.on("event_name")` decorator.

### `login`
Fired when a QR code is available. Use it to request a pairing code instead, if you prefer.
```python
@bot.on("login")
def onLogin(_):
    code = bot.requestPairingCode("201234567890")
```

### `connection`
Fired when the connection opens or closes.
```python
@bot.on("connection")
def onConnection(conn: Connection):
    print(conn.connected, conn.reason)
```

### `message`
Fired for every incoming message that isn't a recognized command.
```python
@bot.on("message")
def onMessage(msg: Message):
    print(msg.text, msg.sender, msg.chat)
```

Useful `Message` attributes: `text`, `sender`, `chat`, `fromMe`, `quoted`, `quotedText`, `phone`, and methods `reply()`, `send()`, `delete()`.

### `command`
Fired when a message starts with one of your configured prefixes.
```python
@bot.on("command")
def onCommand(cmd: Command):
    print(cmd.name, cmd.args)
```

### `reaction`
Fired when someone reacts to (or removes a reaction from) a message.
```python
@bot.on("reaction")
def onReaction(react: Reaction):
    print(react.emoji, react.removed, react.sender)
```

`react.msg` gives you the original `Message` object that was reacted to, resolved from Wazpy's built-in message cache — even across restarts.

### `shutdown`
Fired once, right before the bot shuts down (e.g. on `Ctrl+C`). Useful for sending a farewell message.
```python
@bot.on("shutdown")
def onShutDown(lastMsg: Message):
    if lastMsg:
        lastMsg.send("Goodbye!")
```

You can also set a custom shutdown message that Wazpy sends automatically to the last active chat:
```python
bot.shutdownMsg = "The bot is going offline!"
```

---

## Pairing Code Login

Instead of scanning a QR code every time, you can request a pairing code:

```python
code = bot.requestPairingCode("201234567890")
print(f"Enter this code in WhatsApp: {code}")
```

Optionally pass a custom 8-character code (uppercase letters and digits only):
```python
code = bot.requestPairingCode("201234567890", customPairingCode="ABCD1234")
```

---

## Requirements

- Python 3.9+
- Node.js (installed and available in your system's `PATH`)

---

## License

*(No license specified yet — add one here, e.g. MIT, before publishing.)*

---

## Contributing

Issues and pull requests are welcome. If you run into a bug or have a feature idea, feel free to open an issue.