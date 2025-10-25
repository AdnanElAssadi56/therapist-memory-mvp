# AI Therapist Memory System

A minimal AI therapist with an LLM-powered memory system that maintains context across multiple conversation sessions.

## Overview

This system uses GPT-5 to power both the therapist conversations and the memory management. The LLM intelligently decides what information is important to remember and what past context is relevant for each conversation.

## Setup

1. Create and activate virtual environment:
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Unix/MacOS
source .venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

## Usage

Start a new therapy session:
```bash
python main.py
```

Continue with existing client:
```bash
python main.py --client-id <client_id>
```

## Project Structure

```
.
├── main.py                 # CLI entry point
├── therapist.py            # Conversation loop and session management
├── memory_manager.py       # LLM-powered memory extraction and retrieval
├── storage.py              # JSON file I/O utilities
├── prompts.py              # LLM prompts and context formatting
└── data/
    └── clients/
        └── {client_id}/
            ├── profile.json       # Core facts (always loaded)
            ├── themes.json        # Emotional patterns and recurring topics
            └── sessions/
                └── session_XXX.json  # Full session transcripts
```

## Memory System Design

### Architecture

The memory system uses a **two-stage LLM approach**:

1. **Memory Retrieval** (before each response)
   - LLM analyzes the user's message
   - Decides which past themes and sessions are relevant
   - Loads only relevant context to avoid noise

2. **Memory Extraction** (after each session)
   - LLM reviews the full session transcript
   - Extracts important facts, themes, and patterns
   - Updates profile.json and themes.json

### Memory Types

- **Profile** (`profile.json`): Core biographical facts, current goals, key information
- **Themes** (`themes.json`): Recurring emotional patterns, progress markers, therapy focus areas
- **Sessions** (`session_XXX.json`): Full transcripts with summaries and extracted insights

### Why LLM-Powered?

Instead of naive keyword matching, the LLM understands:
- Semantic meaning and context
- What's therapeutically important
- Connections between themes across sessions
- When past context is relevant

This creates a more natural and effective memory system.
