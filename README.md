# Wazpy

**Wazpy** is a Python library for building WhatsApp bots with a clean, event-driven API powered by [Baileys](https://github.com/WhiskeySockets/Baileys) under the hood. It gives you full control over messages, commands, reactions, and connection events — with an easy-to-use decorator-based syntax and built-in customization options.

Wazpy runs a lightweight Node.js server internally (bundled with the package) that talks to WhatsApp via Baileys, while you write all your bot logic in plain Python.

[CHANGELOG.md](./ChangeLog.md)

---

## Features

- 🎯 **Event-driven API** — simple `@bot.on(...)` decorators for every event
- 💬 **Command system** — built-in prefix-based command parsing (e.g. `.echo`, `.help`)
- 😀 **Reaction handling** — detect when users react to (or remove a reaction from) a message, with automatic lookup of the original message
- 🔐 **Pairing code & QR login** — connect without scanning a QR code if you prefer
- 🗂️ **Persistent message cache** — reactions can resolve the original message even after a restart
- 👋 **Graceful shutdown** — send a custom "goodbye" message when your bot shuts down
- ⚙️ **Highly configurable** — logger level, auth folder, browser identity, command case-sensitivity, cache location, and more

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
from wazpy.utils import QRCode, Message, Command, Connection, Reaction

bot = WhatsAppSocket(
    authName="auth",
    cacheFileName="cache",
    dataDir=".wazpy",
    saveCache=True,
    loggerLevel="silent",
    syncFullHistory=False,
    browserInfo=Browser.ubuntu("Chrome"),
    commandPrefixs=["."],
    commandCaseSens=False,
    nodeJSPort="default",
    nodeJSHost="default",
)

def main():

    @bot.on("login")
    def onLogin(qr: QRCode):
        # scan in the terminal
        qr.render(small=True)
        # or request a pairing code instead:
        # code = bot.requestPairingCode("201234567890")
        # print(f"Your pairing code is: {code}")

    @bot.on("connection")
    def onConnection(conn: Connection):
        if conn.connected:
            print("Connected!")
        else:
            print(f"Disconnected ({conn.reason})")
            if conn.isAuthFailure():
                print("Logged out — delete the auth folder and scan again.")

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
        if react.msg is None or not react.msg.fromMe:
            return
        if react.removed:
            return

        if react.emoji == "🗑️":
            react.msg.delete()

    @bot.on("shutdown")
    def onShutDown(lastMsg: Message):
        if not Message.isMessage(lastMsg):
            return
        lastMsg.send("Bot is shutting down. Goodbye!")

    bot.start()

if __name__ == "__main__":
    main()
```

Run the script, scan the QR code (or use a pairing code), and your bot is live. Press `Ctrl+C` to stop it gracefully — Wazpy will send your shutdown message before exiting.

---

## `WhatsAppSocket(...)` — Configuration Options

| Parameter | Type | Default | Description |
|---|---|---|---|
| `authName` | `str` | `"auth"` | Folder name (inside `dataDir`) where session credentials are stored |
| `cacheFileName` | `str` | `"cache.db"` | File name for the persistent message cache. A `.db` extension is added automatically if missing |
| `dataDir` | `str` | `".wazpy"` | Folder where the auth session and message cache are stored |
| `saveCache` | `bool` | `True` | Whether the message cache should persist to disk. If `False`, cached messages are lost on restart |
| `loggerLevel` | `str` | `"silent"` | Baileys logger level: `debug`, `error`, `fatal`, `info`, `silent`, `trace`, or `warn` |
| `syncFullHistory` | `bool` | `False` | Whether to sync full chat history on connect |
| `browserInfo` | `list` | `Browser.ubuntu("Chrome")` | Browser identity shown to WhatsApp (see [`Browser`](#browser) below) |
| `commandPrefixs` | `list[str]` | `["."]` | List of single special-character prefixes that trigger the `command` event (e.g. `["!", "."]`) |
| `commandCaseSens` | `bool` | `True` | Whether command names are case-sensitive |
| `nodeJSPort` | `int` \| `"default"` | `"default"` | Port used for the internal Python ↔ Node.js connection. `"default"` resolves to `5000` |
| `nodeJSHost` | `str` | `"default"` | Host for the internal connection. `"default"` → `127.0.0.1`, `"all"` → `0.0.0.0` |

All parameters are validated on init — passing the wrong type or an invalid value (e.g. an unknown `loggerLevel`, or a multi-character prefix) raises a `TypeError` or `ValueError` immediately.

---

## Events Reference

Register any event with the `@bot.on("event_name")` decorator.

### `login`
Fired when a QR code becomes available. The callback receives a [`QRCode`](#qrcode) object.
```python
@bot.on("login")
def onLogin(qr: QRCode):
    qr.render(small=True)       # print it in the terminal
    # or: qr.saveImg("qr.png")  # save it as an image instead
```

### `connection`
Fired when the connection opens or closes. The callback receives a [`Connection`](#connection) object.
```python
@bot.on("connection")
def onConnection(conn: Connection):
    print(conn.connected, conn.reason, conn.statusCode)
```

### `message`
Fired for every incoming message that isn't a recognized command. The callback receives a [`Message`](#message-1) object.
```python
@bot.on("message")
def onMessage(msg: Message):
    print(msg.text, msg.sender, msg.chat)
```

### `command`
Fired when a message starts with one of your configured prefixes. The callback receives a [`Command`](#command) object.
```python
@bot.on("command")
def onCommand(cmd: Command):
    print(cmd.name, cmd.args)
```

### `reaction`
Fired when someone reacts to (or removes a reaction from) a message. The callback receives a [`Reaction`](#reaction) object.
```python
@bot.on("reaction")
def onReaction(react: Reaction):
    print(react.emoji, react.removed, react.sender)
```

`react.msg` gives you the original `Message` object that was reacted to, resolved from Wazpy's built-in message cache — even across restarts (as long as `saveCache=True` and the message was seen while the cache held it).

### `shutdown`
Fired once, right before the bot shuts down (e.g. on `Ctrl+C`). The callback receives the last `Message` the bot saw (or `None` if none was ever received).
```python
@bot.on("shutdown")
def onShutDown(lastMsg: Message):
    if Message.isMessage(lastMsg):
        lastMsg.send("Goodbye!")
```

You can also set a custom shutdown message that Wazpy sends automatically to the last active chat when the bot exits:
```python
bot.shutdownMsg = "The bot is going offline!"
```

---

## Classes Reference

### `Message`

Represents an incoming WhatsApp message.

| Attribute | Description |
|---|---|
| `valid` | `True` if the object wraps a real message. Always check this (or use `Message.isMessage(msg)`) before using other attributes |
| `id` | The message's unique ID |
| `fromMe` | `True` if the bot itself sent this message |
| `timestamp` | Unix timestamp of the message |
| `name` | The sender's push name (display name) |
| `chat` | JID of the chat the message belongs to |
| `sender` | JID of the person who sent it (participant in groups, or `chat` in DMs) |
| `senderNumber` | Sender JID resolved to a real phone-number JID when possible |
| `phone` | The sender's raw phone number as a string, or `None` if it can't be resolved (e.g. `@lid` JIDs) |
| `text` | The message text, or `None` for non-text messages |
| `quoted` / `quotedText` / `quotedSender` / `quotedFromMe` | Details of a quoted/replied-to message, if any |
| `data` | The raw underlying message dict from Baileys |

**Methods**
```python
msg.reply(text, chat=None, quoted=None)   # reply, quoting this message by default
msg.send(text, chat=None)                 # send a new message (not a reply)
msg.delete(key=None)                      # delete this message (works on the bot's own messages, or any message if the bot is a group admin)
```

Each of `reply`, `send`, and `delete` raises a `RuntimeError` if the underlying action fails (e.g. not connected, invalid chat).

**Static helper**
```python
Message.isMessage(msg)   # True if msg is not None and msg.valid — safe to call even with None
```

### `Command`

Represents a message that matched one of your configured prefixes.

| Attribute | Description |
|---|---|
| `msg` | The underlying `Message` object |
| `name` | The command name (text right after the prefix, e.g. `"echo"` for `.echo hi`) |
| `args` | A list of the remaining words after the command name |

### `Connection`

Represents a connection state change.

| Attribute | Description |
|---|---|
| `connected` | `True` if the connection just opened, `False` if it closed |
| `statusCode` | The disconnect status code, if any |
| `reason` | The disconnect reason message, if any |

**Methods**
```python
conn.isAuthFailure()   # True if statusCode == 401 (session logged out / invalid — requires re-scanning)
```

### `QRCode`

Represents a QR code emitted during login.

**Methods**
```python
qr.render(small=True)              # print the QR code directly in the terminal
qr.saveImg(imgName="qr.png", imgWidth=500)   # save the QR code as a PNG image
```

### `Reaction`

Represents a reaction (emoji) added to, or removed from, a message.

| Attribute | Description |
|---|---|
| `valid` | `True` if the object wraps a real reaction |
| `emoji` | The reaction emoji, or `""` if the reaction was removed |
| `removed` | `True` if this event represents the reaction being removed |
| `sender` | JID of whoever reacted |
| `fromMe` | `True` if the bot itself sent the reaction |
| `ogMsgId` / `ogMsgChat` / `ogMsgFromMe` | Identifiers for the original message that was reacted to |
| `msg` | The original `Message` object being reacted to, resolved from the message cache, or `None` if it isn't in the cache |

### `Browser`

Helper for building the `browserInfo` value passed to `WhatsAppSocket`.

```python
Browser.ubuntu("Chrome")
Browser.windows("Chrome")
Browser.macOS("Chrome")
```

Each returns a `[platform, browser, ""]` list in the format Baileys expects.

---

## `WhatsAppSocket` Methods

```python
bot.requestPairingCode(phoneNumber, customPairingCode=None)
```
Requests a pairing code instead of scanning a QR code. `phoneNumber` should include the country code, no `+` or spaces (e.g. `"201234567890"`). `customPairingCode`, if given, must be exactly 8 characters (uppercase letters and digits only).

```python
bot.shutdownMsg = "Goodbye!"   # setter
bot.shutdownMsg                # getter — returns the currently set message, or None
```
Sets/gets the message automatically sent to the last active chat when the bot shuts down.

```python
bot.getConfig()       # returns the internal Node.js server config dict
bot.getConfigPath()   # returns the path to the internal config.json file
```

```python
bot.start()
```
Connects the bot and blocks the main thread until `Ctrl+C` is pressed, at which point it runs your `shutdown` callback (if any) and exits cleanly.

---

## Persistent Message Cache

Wazpy keeps a small on-disk cache (using Python's `dbm`) of recently seen messages, keyed by message ID. This is what allows the `reaction` event's `react.msg` to resolve the full original `Message` — including its text and sender — even if the bot was restarted between the original message and the reaction.

- Controlled by `saveCache` (on/off), `cacheFileName`, and `dataDir` in `WhatsAppSocket(...)`.
- Stored at `<dataDir>/<cacheFileName>` (default: `.wazpy/cache.db`).
- If `saveCache=False`, the cache lives in memory only and is cleared on restart.

---

## Requirements

- Python 3.9+
- Node.js (installed and available in your system's `PATH`)

---

## License

MIT

---

## Contributing

Issues and pull requests are welcome. If you run into a bug or have a feature idea, feel free to open an issue.

## Change Log