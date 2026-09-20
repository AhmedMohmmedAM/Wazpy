const pino = require("pino");
const {
    makeWASocket,
    fetchLatestBaileysVersion,
    useMultiFileAuthState,
    DisconnectReason,
    Browsers
} = require("@whiskeysockets/baileys");
const qrcode = require("qrcode-terminal");
const QRcode = require("qrcode");
const fs = require("fs");
const path = require("path");
const net = require("net");

const { isAuthValid } = require("./assets/isauthvalid");
const { resolveBrowser } = require("./assets/resolvebrowser");

const CONFIG_PATH = path.join(__dirname, "config.json");
const config = JSON.parse(fs.readFileSync(CONFIG_PATH, "utf8"));

var loggerLevel = "silent";
var authName = "auth";
var dataDir = ".wazpy";
var browserInfo = ["ubuntu", "Chrome", "14.4.1"];
var syncFullHistory = false;

var globalSocket;
var shutdownMsg = null;
var lastChat = null;

var _PREFIXS = [];
var _CASESENS = false;

function send(socket, message) {
    socket.write(JSON.stringify(message) + "\n");
}

async function startBaileys(logger, authName, browserInfo, socket) {
    const fullAuthPath = path.join(dataDir, authName);

    if (fs.existsSync(fullAuthPath) && !isAuthValid(fullAuthPath)) {
        fs.rmSync(fullAuthPath, { recursive: true, force: true });
    }
    const { state, saveCreds } = await useMultiFileAuthState(fullAuthPath);
    const { version } = await fetchLatestBaileysVersion();

    const sock = makeWASocket({
        auth: state,
        logger,
        version,
        browser: resolveBrowser(browserInfo, Browsers),
        syncFullHistory,
    });
    globalSocket = sock;

    sock.ev.on("creds.update", saveCreds);

    sock.ev.on("connection.update", async (update) => {
        const { qr, connection, lastDisconnect } = update;

        if (qr) {
            send(socket, {
                type: "event",
                event: "login",
                qr
            });
        }

        switch (connection) {
            case "open":
                send(socket, {
                    type: "event",
                    event: "connection",
                    status: "open"
                });
                break;

            case "close":
                const shouldReconnect = lastDisconnect?.error?.output?.statusCode;

                send(socket, {
                    type: "event",
                    event: "connection",
                    status: "close",
                    reason: lastDisconnect?.error?.message,
                    statusCode: shouldReconnect
                });

                if (shouldReconnect !== DisconnectReason.loggedOut) {
                    await startBaileys(logger, authName, browserInfo, socket);
                } else {
                    console.log("\n[\x1b[1;33mNodeJS-Server\x1b[0m] \x1b[31mLogged out from the bot\x1b[0m\n  \x1b[90m- Ending process and socket\n  - Delete auth file and relogin\n\x1b[0m")
                    socket.end();
                    process.exit(0);
                }

                break;
        }
    });

    sock.ev.on("messages.upsert", (data) => {
        if (!data.messages || data.messages.length === 0) return;
        const message = data.messages[0];
        
        if(message.message?.reactionMessage) {
            send(socket, {
                type: "event",
                event: "reaction",
                reaction: [{
                    key: message.key,
                    reaction: message.message.reactionMessage
                }]
            });
            return;
        }

        const text = message.message?.conversation ||
                     message.message?.extendedTextMessage?.text;
        lastChat = message.key?.remoteJid;
        
        if (text && _PREFIXS.includes(text[0])) {
            const parts = text.trim().split(/\s+/);
            const command = !_CASESENS
                          ? parts[0].slice(1)
                          : parts[0].slice(1).toLowerCase();
            const args = parts.slice(1);

            send(socket, {
                type: "event",
                event: "command",
                command: {name: command, args},
                message: data
            });
        } else {
            send(socket, {
                type: "event",
                event: "message",
                message: data
            });
        }
    });

    sock.ev.on("messages.reaction", (reaction) => {
        send(socket, {
            type: "event",
            event: "reaction",
            reaction
        });
    });
}

const server = net.createServer((socket) => {
    let buffer = "";
    let processing = false;
    const queue = [];

    socket.on("error", (err) => {
        if (err.code == "ECONNRESET") {
            console.error("[\x1b[1;33mNodeJS-Server\x1b[0m] Wazpy-Client is not connected use 'start()' in 'WhatsAppSocket()'");
        } else {
            console.error("[\x1b[1;33mNodeJS-Server\x1b[0m] Socket error: ", err.message);
        }
        process.exit(1);
    });

    socket.on("close", () => {
        console.log("[\x1b[1;33mNodeJS-Server\x1b[0m] Connection with Python client closed.");
        process.exit(1);
    });

    async function processBuffer() {
        if (processing) return;
        processing = true;

        while (buffer.includes("\n")) {
            const index = buffer.indexOf("\n");
            const line = buffer.slice(0, index);
            buffer = buffer.slice(index + 1);

            if (!line) continue;

            let message;
            try {
                message = JSON.parse(line);
            } catch (e) {
                console.log("Invalid JSON:", line);
                continue;
            }

            if (message.action === "setup") {
                loggerLevel = message.loggerLevel;
                authName = message.authName;
                dataDir = message.dataDir;
                syncFullHistory = message.syncFullHistory;
                browserInfo = message.browserInfo;
                _PREFIXS = message.prefixs;
                _CASESENS = message.casesens;
                send(socket, { type: "response", success: true, message: "" });
            }

            if (message.action === "start") {
                await startBaileys(pino({ level: loggerLevel }), authName, browserInfo, socket);
                send(socket, { type: "response", success: true, message: "" });
            }

            if (message.action === "replyMessage") {
                try {
                    if (!globalSocket) {
                        send(socket, { type: "response", success: false, message: "Not connected" });
                    } else {
                        if (!message.chat) {
                            send(socket, { type: "response", success: false, message: "Chat is required" });
                        } else {
                            await globalSocket.sendMessage(
                                message.chat,
                                { text: message.msg },
                                { quoted: message.quoted }
                            );
                            send(socket, { type: "response", success: true, message: "" });
                        }
                    }
                } catch (err) {
                    send(socket, { type: "response", success: false, message: err.message });
                }
            } 

            if (message.action === "sendMessage") {
                try {
                    if (!globalSocket) {
                        send(socket, { type: "response", success: false, message: "Not connected" });
                    } else {
                        await globalSocket.sendMessage(
                            message.chat,
                            { text: message.msg },
                        );
                        send(socket, { type: "response", success: true, message: "" });
                    }
                } catch (err) {
                    send(socket, { type: "response", success: false, message: err.message });
                }
            }

            if (message.action === "deleteMessage") {
                try {
                    if (!globalSocket) {
                        send(socket, { type: "response", success: false, message: "Not connected" });
                    } else {
                        await globalSocket.sendMessage(
                            message.chat,
                            { delete: message.key },
                        );
                        send(socket, { type: "response", success: true, message: "" });
                    }
                } catch (err) {
                    send(socket, { type: "response", success: false, message: err.message });
                }
            }

            if (message.action === "qrcodeGenerate") {
                if (message.type === "img") {
                    QRcode.toFile(message.fileName, message.qr, { width: message.fileWidth }, (err) => {
                        if (err) {
                            send(socket, { type: "response", success: false, message: err.message });
                        } else {
                            send(socket, { type: "response", success: true, message: "" });
                        }
                    });
                } else if (message.type === "terminal") {
                    qrcode.generate(message.qr, { small: message.small });
                    send(socket, { type: "response", success: true, message: "" });
                }
            }

            if (message.action === "requestPairCode") {
                try {
                    if (!globalSocket) {
                        send(socket, { type: "response", success: false, message: "Not connected" });
                    } else {
                        if (globalSocket.authState.creds.registered) {
                            send(socket, { type: "response", success: false, message: "Already registered, no need for pairing code" });
                        } else {
                        
                            const code = message.customPairingCode
                                ? await globalSocket.requestPairingCode(message.phoneNumber, message.customPairingCode)
                                : await globalSocket.requestPairingCode(message.phoneNumber);

                            send(socket, { type: "response", success: true, message: "", code });
                        }
                    }
                } catch (err) {
                    send(socket, { type: "response", success: false, message: err.message });
                }
            }

            if (message.action == "changeShutDownMsg") {
                shutdownMsg = message.message;
                send(socket, { type: "response", success: true, message: "" });
            }

            if (message.action == "sendShutdownMsg") {
                if (!globalSocket) {
                    send(socket, { type: "response", success: false, message: "Not connected" });
                } else {
                    if (!shutdownMsg) {
                        console.log("[\x1b[1;33mNodeJS-Server\x1b[0m] No shutdownMsg was detected");
                        send(socket, { type: "response", success: true, message: "" });
                    } else {
                        await globalSocket.sendMessage(
                            lastChat,
                            { text: shutdownMsg }
                        );
                        console.log("[\x1b[1;33mNodeJS-Server\x1b[0m] Sended shutdownMsg successfully");
                        send(socket, { type: "response", success: true, message: "" });
                    }
                }
            }
        }

        processing = false;
    }

    socket.on("data", (data) => {
        buffer += data.toString();
        processBuffer();
    });
});

server.listen(config["serverPort"], config["serverHost"],  () => {
    console.log(`[\x1b[1;33mNodeJS-Server\x1b[0m] Started on ${config["serverHost"]}:\x1b[36m${config["serverPort"]}\x1b[0m port`);
});

process.on('SIGTERM',  () => {
    process.exit(0);
});