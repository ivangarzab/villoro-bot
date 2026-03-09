# CLAUDE.md — AI Assistant Context Guide

## Project Overview

**Project:** VilloroBot — Discord bot for academic study of *Knowledge and Freedom in the Work of Luis Villoro*
**Language:** Python 3.9+
**Architecture:** Modular Discord.py bot backed by a RAG engine (kluvs-brain)
**Repository:** https://github.com/ivangarzab/villoro-bot

### Purpose

VilloroBot helps students explore the Villoro book through Socratic dialogue. Instead of providing direct answers, it returns conceptual hints, page citations, and thought-provoking follow-up questions. Powered by `kluvs-brain` (RAG over a Supabase/pgvector store with OpenAI).

---

## Project Structure

```
villoro-bot/
├── main.py                     # Entry point — creates VilloroBot and calls bot.run()
├── bot.py                      # VilloroBot class (discord.Client subclass)
├── config.py                   # BotConfig — loads and validates .env variables
├── cogs/
│   ├── general_commands.py     # /help, /usage slash commands
│   └── brains_commands.py      # /ask-privately slash command (ephemeral RAG)
├── events/
│   └── message_handler.py      # on_message: @mention (public) and DM modes
├── services/
│   └── brains_service.py       # Wraps KluvsAgenticEngine + SocraticAgent; owns history
├── utils/
│   ├── constants.py            # BOOK_TITLE, BOOK_SCOPE, FEEDBACK_PERCENTAGE, GENERIC_ERRORS
│   ├── interaction_logger.py   # Daily CSV logging (interactions + reactions)
│   └── feedback.py             # FeedbackView — 👍/👎 buttons on public/DM responses
├── tests/
│   ├── test_brains_commands.py
│   ├── test_general_commands.py
│   ├── test_interaction_logger.py
│   ├── test_message_handler.py
│   └── run_tests.py
├── logs/                       # Auto-created; daily CSV files
├── Makefile
└── requirements.txt
```

---

## Architecture

### Composition Pattern (kluvs-brain)

```
BrainsService
  └── SocraticAgent
        └── KluvsAgenticEngine  ← ReAct loop (route → search → think → synthesize)
```

- `KluvsAgenticEngine` + `SocraticAgent` are instantiated **once at startup** in `BrainsService.__init__()`.
- **Never** create a new engine/agent per message — it's expensive.
- `BrainsService.ask(user_id: int, question: str) -> str` is the only public entry point.

### Per-User History

`BrainsService` maintains `_history: Dict[int, List[Dict[str, str]]]` keyed by Discord user ID.
- History is passed to `agent.ask(..., history=history)` on every call.
- Updated (user + assistant turns appended) **only on success**, never on error.
- Capped at 20 messages (10 Q&A pairs) via `MAX_HISTORY = 20`.

### Interaction Modes

| Mode | Trigger | Feedback buttons |
|------|---------|-----------------|
| `public` | @mention in server channel | Yes (FEEDBACK_PERCENTAGE chance) |
| `dm` | Direct message to bot | Yes |
| `private` | `/ask-privately` slash command | No (ephemeral) |

### "Thinking..." UX

The agentic engine takes ~4–8 seconds. For `public` and `dm` modes:
1. Send `"Thinking..."` immediately → capture `thinking_msg`
2. Await `brains_service.ask()`
3. Edit `thinking_msg` with the response (and optional FeedbackView)

For `private` mode, `defer(ephemeral=True)` handles the loading state.

---

## Core Components

### `services/brains_service.py`
- **`BrainsService(supabase_url, supabase_key, openai_key)`** — init the engine stack
- **`ask(user_id, question) -> str`** — main RAG call with history injection
- **`_update_history(user_id, question, response)`** — appends turns, enforces cap

### `events/message_handler.py`
- **`setup_message_handlers(bot)`** — registers `on_message` event
- **`_handle_ask(bot, message, question, mode, guild_id)`** — shared public/DM logic
- **`_split_response(text) -> list[str]`** — safety guard for Discord's 2000-char limit

### `utils/interaction_logger.py`
- Logs every interaction to `logs/interactions_YYYY-MM-DD.csv`
- Logs reactions to `logs/reactions_YYYY-MM-DD.csv`
- Join key: `message_id`
- `conversation_id` and `tokens_used` columns are null placeholders for future features

### `utils/constants.py`
```python
BOOK_TITLE = "Knowledge and Freedom in the Work of Luis Villoro"
BOOK_SCOPE = "montemayor_villoro"   # Supabase vector store scope filter
FEEDBACK_PERCENTAGE = 0.3           # 30% chance of attaching feedback buttons
```

---

## Environment Variables

```bash
TOKEN=<discord_bot_token>
BRAINS_SUPABASE_URL=https://your-project.supabase.co
BRAINS_SUPABASE_KEY=<service_role_key>
KEY_OPEN_AI=sk-...
```

---

## Commands Reference

| Command | Type | Description |
|---------|------|-------------|
| `/ask-privately <question>` | Slash | Ephemeral RAG response (only requester sees it) |
| `/help` | Slash | Getting started guide |
| `/usage` | Slash | List all commands |
| @mention `<question>` | Message | Public RAG response in channel |
| DM `<question>` | Message | RAG response in DM |

---

## Testing

**Framework:** `unittest.IsolatedAsyncioTestCase`
**Run:** `make test` or `.venv/bin/python -m unittest discover -s tests -v`

All Discord objects are mocked (`AsyncMock`, `MagicMock`). `brains_service.ask` is always mocked — tests do not hit real APIs.

Key patterns:
- `thinking_msg = message.channel.send.return_value` — access the "Thinking..." message mock
- Check response delivery via `thinking_msg.edit.call_args`, not `channel.send.call_args`
- Error paths still call `log_interaction` — assert `error_type` in `call_args[1]`

---

## Development Workflow

```bash
make install        # Create .venv and install all dependencies
make test           # Run test suite
make coverage       # Run tests with terminal coverage report
make run            # Start the bot
make update-brain   # Force reinstall kluvs-brain from GitHub
make run-fresh      # update-brain + run
make clean          # Remove .venv, __pycache__, coverage files
```

**Local kluvs-brain development:** install editable to avoid pushing for every change:
```bash
.venv/bin/pip install -e ../kluvs-brain
```
Switch back to the git dep with `make update-brain` when kluvs-brain is stable.

---

## Key Conventions

- **No Discord embeds** — all responses are plain text
- **No direct answers** — kluvs-brain's SocraticAgent enforces Socratic style
- **Privileged intents required** in Discord Developer Portal: `message_content`, `members`
- **Keep it simple** — villoro-bot is intentionally lean; avoid adding features beyond its scope
- Always update `CLAUDE.md` if the architecture changes

---

## Quick Reference

| Thing | Location |
|-------|----------|
| Bot class | `bot.py::VilloroBot` |
| Entry point | `main.py` |
| Config/env | `config.py::BotConfig` |
| RAG service | `services/brains_service.py::BrainsService` |
| Public/DM handler | `events/message_handler.py` |
| Slash commands | `cogs/brains_commands.py`, `cogs/general_commands.py` |
| Constants | `utils/constants.py` |
| Run tests | `make test` |
| Update kluvs-brain | `make update-brain` |
