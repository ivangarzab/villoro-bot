# VilloroBot

A Discord bot that acts as an expert on *Knowledge and Freedom in the Work of Luis Villoro* by Professor Carlos Montemayor.

## What is this?

VilloroBot is powered by [kluvs-brain](https://github.com/ivangarzab/kluvs-brain), a RAG (Retrieval-Augmented Generation) system that ingests the Villoro book and makes it queryable through natural language. Students can ask the bot questions about the book, get conceptual guidance, and use it as a writing aid — all through Discord slash commands.

The bot responds in a Socratic style: offering hints, conceptual anchors, and thought-provoking follow-up questions rather than direct answers, always citing page references from the actual text.

## Tech stack

- [discord.py](https://discordpy.readthedocs.io/) — Discord bot framework
- [kluvs-brain](https://github.com/ivangarzab/kluvs-brain) — RAG engine (OpenAI + Supabase pgvector)
- Python 3.9+

## Setup

```bash
make install   # Create venv and install dependencies
cp .env.example .env  # Fill in your credentials
make run       # Start the bot
```

## Commands

| Command | Description |
|---------|-------------|
| `/ask-privately <question>` | Ask a question — only you see the answer (ephemeral) |
| `/help` | Getting started guide |
| `/usage` | List all available commands |
| @mention `<question>` | Ask publicly in a server channel |
| DM `<question>` | Ask privately via direct message |

## Conversation context

VilloroBot maintains conversation history in **DMs and threads**, so the bot remembers earlier turns and can build on them. In public server channels, each question is answered fresh — this prevents unrelated student questions from contaminating each other's context. Starting a thread from a bot response automatically seeds the thread with that message as initial context.

## Development

```bash
make test       # Run test suite
make coverage   # Run tests with coverage report
make run-fresh  # Update kluvs-brain and run the bot
```
