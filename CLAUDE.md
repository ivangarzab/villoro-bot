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
- `BrainsService.ask(user_id: int, channel_id: Optional[int], question: str) -> AskResult` is the only public entry point.

### Conversation History

History is scoped to the **channel** (`channel_id`), not the user. The policy for whether history is used depends on the interaction mode:

| Mode | `channel_id` passed | History behaviour |
|------|---------------------|-------------------|
| `public` (@mention) | `None` | Stateless — each question answered fresh |
| `dm` | DM channel ID | Per-user (DM channel is naturally unique per user) |
| `thread` (@mention) | Thread channel ID | Shared by all students in the thread |
| `private` (`/ask-privately`) | `None` | Stateless (ephemeral, no shared context) |

Additional rules:
- History is passed to `agent.ask(..., history=history)` on every stateful call.
- Updated (user + assistant turns appended) **only on success**, never on error.
- Capped at 20 messages (10 Q&A pairs) via `MAX_HISTORY = 20`.
- `ask()` returns `AskResult(response: str, conversation_id: Optional[str])`. `conversation_id` is `None` in stateless mode.

### Thread Seeding

When the first message arrives in a thread with no existing session, `message_handler` fetches the thread's starter message (thread ID == starter message ID in Discord) and seeds the session via `BrainsService.seed_session()`. The starter message is injected as the first history entry with role `'assistant'` or `'user'` depending on its author. If the fetch fails, the thread proceeds without seeding (silent no-op).

### Interaction Modes

| Mode | Trigger | Feedback buttons |
|------|---------|-----------------|
| `public` | @mention in server channel | Yes (FEEDBACK_PERCENTAGE chance) |
| `dm` | Direct message to bot | Yes |
| `thread` | @mention inside a thread | Yes (FEEDBACK_PERCENTAGE chance) |
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
- **`ask(user_id, channel_id, question) -> AskResult`** — main RAG call; `channel_id=None` for stateless mode
- **`has_session(channel_id) -> bool`** — check if a conversation session exists for a channel
- **`seed_session(channel_id, content, role)`** — inject a starter message as initial thread context
- **`_get_session(channel_id)`** — return or create `(history, conversation_id)` for a channel
- **`_update_history(channel_id, question, response)`** — appends turns, enforces cap

### `events/message_handler.py`
- **`setup_message_handlers(bot)`** — registers `on_message` event
- **`_handle_ask(bot, message, question, mode, guild_id)`** — shared public/DM logic
- **`_split_response(text) -> list[str]`** — safety guard for Discord's 2000-char limit

### `utils/interaction_logger.py`
- Logs every interaction to `logs/interactions_YYYY-MM-DD.csv`
- Logs reactions to `logs/reactions_YYYY-MM-DD.csv`
- Join key: `message_id`
- `conversation_id` is populated for DMs and threads; `None` for stateless modes (public, private)
- `tokens_used` is a null placeholder for future kluvs-brain usage tracking

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
