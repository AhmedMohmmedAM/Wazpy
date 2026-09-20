# WAsock

![WAsock Logo](assets/logo.png)

**WAsock** (WhatsApp Socket) is a lightweight Python library for interacting with WhatsApp, built on top of [Baileys](https://github.com/WhiskeySockets/Baileys) via a Node.js subprocess that communicates with Python over a TCP socket.

Made by an Egyptian developer 🇪🇬 — Ahmed Mohmmed-AM.

> **Status:**`0.5.3-Beta` — still under development. The API may change before a stable release.

---

## Overview

WAsock provides a simple Python interface for interacting with WhatsApp without writing JavaScript.

It supports:

* Receiving messages
* Sending messages
* Replying to messages
* Deleting messages
* Quoted/replied message information
* QR code login
* Pairing code login
* Connection status handling
* Custom browser information
* Full history synchronization

WAsock is built on top of [Baileys](https://github.com/WhiskeySockets/Baileys). It runs Baileys in a Node.js subprocess and communicates with it through a local TCP socket, allowing WhatsApp functionality to be controlled entirely from Python.

---

## Requirements

* Python >= 3.8
* Node.js >= 18 recommended
* An internet connection to install the required npm dependencies

---

## Installation

```bash
pip install wasock
```

---

## Quick Start

```python
from wasock import WhatsAppSocket, Message, QRCode, Connection, Browser

bot = WhatsAppSocket(
    authName="auth",
    loggerLevel="silent",
    browserInfo=Browser.ubuntu("Chrome"),
    syncFullHistory=False
)

def onLogin(data):
    qr = QRCode(
        data["qr"],
        bot.nodeJS,
        small=True,
        type="img",
        imgWidth=500
    )
    qr.render("qr.png")
    print("Scan qr.png with WhatsApp on your phone")

def onConnection(data):
    conn = Connection(data)

    if conn.connected:
        print("Connection opened!")
    else:
        print(f"Connection closed: {conn.reason}")

def onMessage(data):
    message = Message(data, bot.nodeJS)

    if message.fromMe:
        return

    if message.text == "!ping":
        message.reply("pong")

bot.on("login", onLogin)
bot.on("connection", onConnection)
bot.on("message", onMessage)

bot.start()
```

---

# API

## `WhatsAppSocket`

```python
WhatsAppSocket(
    authName="auth",
    loggerLevel="silent",
    browserInfo=Browser.ubuntu("Chrome"),
    syncFullHistory=False
)
```

Creates a WhatsApp connection and configures the Node.js backend.

### Parameters


| Parameter         | Description                              |
| ----------------- | ---------------------------------------- |
| `authName`        | Name/path of the authentication folder   |
| `loggerLevel`     | Pino logger level                        |
| `browserInfo`     | Browser information used by Baileys      |
| `syncFullHistory` | Whether to synchronize full chat history |

### Methods

* `.start()` — starts the WhatsApp connection.
* `.on(event, callback)` — registers an event listener.
* `.requestPairingCode(phoneNumber, customPairingCode=None)` — requests a pairing code instead of scanning a QR code.
* `.end()` — closes the connection and stops the Node.js process.

`customPairingCode`, when provided, must contain exactly 8 uppercase letters/digits.

---

## `Browser`

Provides predefined browser configurations for Baileys.

Examples:

```python
Browser.ubuntu("Chrome")
Browser.macOS("Chrome")
Browser.windows("Chrome")
```

You can also provide custom browser information:

```python
Browser(
    platform="Ubuntu",
    browser="Chrome",
)
```

The browser information is used as the WhatsApp Web client identity. It does not launch or control an actual web browser (Some times requestPairingCode will not work).

---

## `Message`

A `Message` object is created for each incoming WhatsApp message.

### Properties


| Property        | Description                                          |
| --------------- | ---------------------------------------------------- |
| `.text`         | The message text, or`None`if the message has no text |
| `.chat`         | The chat JID                                         |
| `.key`          | The message key                                      |
| `.fromMe`       | `True`if the message was sent by the bot             |
| `.quoted`       | The quoted message data, if this message is a reply  |
| `.quotedKey`    | The key of the quoted message, if available          |
| `.quotedId`     | The ID of the quoted message                         |
| `.quotedSender` | The sender of the quoted message                     |
| `.quotedFromMe` | Whether the quoted message was sent by the bot       |
| `.quotedText`   | The text of the quoted message, if available         |

### Methods

* `.reply(msg, chat=None, quoted=None)` — replies to the message.
* `.send(msg, chat=None)` — sends a new message without a quote.
* `.delete(messageKey=None)` — deletes a message for everyone.

For example, to delete the message being replied to:

```python
if message.quotedKey:
    message.delete(message.quotedKey)
```

---

## `QRCode`

```python
QRCode(
    data,
    nodeJS,
    small=True,
    type="terminal",
    imgWidth=500
)
```

Handles QR code rendering.

### Parameters


| Parameter  | Description                                       |
| ---------- | ------------------------------------------------- |
| `data`     | The raw QR string received from the`"login"`event |
| `nodeJS`   | The`bot.nodeJS`instance                           |
| `small`    | Compact QR mode for terminal output               |
| `type`     | `"terminal"`or`"img"`                             |
| `imgWidth` | Image width in pixels when using`"img"`           |

`imgWidth` must be an `int`.

### Methods

* `.render(imgName="qr.png")` — renders the QR code.

For `"terminal"`, the QR code is printed directly to the terminal.

For `"img"`, the QR code is saved as an image file.

---

## `Connection`

Represents the current WhatsApp connection state.

### Properties

* `.connected` — `True` if the connection is open.
* `.statusCode` — the disconnect status code, if available.
* `.reason` — the disconnect reason, if available.

### Methods

* `.isAuthFailure()` — returns `True` if the connection closed because of an authentication failure and a new login is required.

---

## Events

WAsock currently provides these events:


| Event          | Description                                          |
| -------------- | ---------------------------------------------------- |
| `"login"`      | Emitted when a QR code is available                  |
| `"connection"` | Emitted when the WhatsApp connection opens or closes |
| `"message"`    | Emitted when a new message is received               |

Example:

```python
bot.on("message", onMessage)
```

---

## Important Notes

* The `auth/` folder contains sensitive WhatsApp session data. **Never commit it to GitHub.**
* The location of `auth/` is resolved relative to the program's current working directory, not the library's installation directory.
* WAsock requires Node.js because Baileys runs inside a Node.js subprocess.
* The API is still under development and may change before the next stable release.

---

## Support

If you need help, have a question, or encounter an issue, you can contact:

**Email:**[wasock.support@gmail.com](https://mail.google.com/mail/?view=cm&fs=1&to=wasock.support@gmail.com)

---

## License

MIT License — see the [LICENSE](https://chatgpt.com/c/LICENSE) file for details.

---

## ChangeLog

See the [ChangeLog](https://chatgpt.com/c/ChangeLog.md) file for the complete change history.

---

## Author

**Ahmed Mohmmed-AM** — Egyptian developer 🇪🇬

GitHub: [@AhmedMohmmed-AM](https://github.com/AhmedMohmmed-AM)
