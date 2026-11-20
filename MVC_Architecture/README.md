# MVC Chatbot (Python)

A small rule-based chatbot ("Bolt") organised with the **Model-View-Controller** pattern.
It has two views, a **console** and a **web page**, driven by the *same* controller and models.

The console version is pure Python 3.10+ standard library. The web view needs Flask.
Run every command below from inside the `MVC_Architecture` folder.

## Setup (for the web view)

```powershell
python -m venv .venv
```
```powershell
.venv\Scripts\python -m pip install -r requirements.txt
```

## Run

Console:
```powershell
python main.py
```

Web (then open http://127.0.0.1:5000):
```powershell
.venv\Scripts\python main.py --web
```

Options: `--port 8000`, `--host 0.0.0.0` (to allow other devices on your network), `--debug` (auto-reload).
Set the `CHATBOT_SECRET_KEY` environment variable to keep browser sessions valid across restarts.

## Test

```powershell
.venv\Scripts\python -m unittest discover -v
```

Without Flask installed, the web tests are skipped and the rest still run.

## Project layout

```
MVC_Architecture/
├── main.py                       # Wires Model + View + Controller together (--web for browser)
├── requirements.txt              # Flask (web view only)
├── chatbot/
│   ├── web_app.py                # Flask routes: HTTP -> controller -> WebView -> JSON
│   ├── models/                   # MODEL: data + logic, no input/output
│   │   ├── bot.py                #   decides replies (intents, learned answers, safe math, time)
│   │   ├── knowledge_base.py     #   intents from JSON + answers taught at runtime
│   │   └── conversation.py       #   message history, save/load to JSON
│   ├── views/                    # VIEW: what the user sees
│   │   ├── base.py               #   ChatView interface every view implements
│   │   ├── console_view.py       #   prints output / reads input, no bot logic
│   │   ├── web_view.py           #   same interface, collects output as JSON events
│   │   └── templates/chat.html   #   the browser chat page
│   ├── controllers/              # CONTROLLER: glue between view and models
│   │   └── chat_controller.py    #   handles /commands and chat messages
│   └── data/intents.json         # Editable list of intents (patterns -> responses)
├── storage/                      # Created at runtime: learned.json, history.json
└── tests/                        # unittest suite for models and controller
```

## How a message flows

1. **View** (`ConsoleView.prompt`) reads a line from the user.
2. **Controller** (`ChatController.handle`) decides if it is a `/command` or chat text.
3. **Model** (`Bot.reply`) works out the answer: taught answer, then math, then best intent, then a fallback.
4. **Controller** stores both messages in the `Conversation` model and tells the **View** to show the reply.

The web view follows the same path. The Flask route passes the browser's text to `ChatController.handle`,
and `WebView` collects what the controller "shows" as JSON events instead of printing them.
The page then renders those events. Neither the models nor the controller changed to support the web.

In the web version each browser has its own conversation (it survives a page reload),
while answers taught with `/teach` are shared by everyone. `/quit` resets your chat.

## Commands

| Command | What it does |
|---|---|
| `/help` | Show help |
| `/teach <question> = <answer>` | Teach a new answer (saved to `storage/learned.json`) |
| `/forget <question>` | Remove a taught answer |
| `/learned` | List taught answers |
| `/history` | Show the conversation |
| `/save` | Save the conversation to `storage/history.json` |
| `/clear` | Clear the conversation |
| `/quit` | Exit |

## Adding new intents

Edit `chatbot/data/intents.json`, then add an object with a `name`, some `patterns` and some `responses`.
`{name}` in a response is replaced by the bot's name.
