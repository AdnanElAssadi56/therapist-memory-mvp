# AI Therapist Memory System

A minimal AI therapist with an LLM-powered memory system that maintains context across multiple conversation sessions.

## Overview

This system uses LLMs to power both the therapist conversations and the memory management. The LLM intelligently decides what information is important to remember and what past context is relevant for each conversation.

**Key Features:**
- Memory extraction from conversations using LLM
- Context-aware responses based on past sessions
- Personalized greetings for returning clients
- Multi-session continuity
- Intelligent memory retrieval

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

**Optional: Adjust speed settings in .env**
- `REASONING_EFFORT=minimal` (fastest, use minimal/low/medium/high)
- `VERBOSITY=low` (more concise, use low/medium/high)

## Usage

### Start a therapy session

**New client (interactive):**
```bash
python main.py
```
The CLI will prompt you to enter a client ID or create a new one.

**Continue with existing client:**
```bash
python main.py --client-id client_abc123
```

**Use different models:**
```bash
python main.py --model gpt-5        # Default
python main.py --model gpt-5-mini   # Faster, cheaper
python main.py --model gpt-5-nano   # Fastest
```

### During a session

- Type your messages naturally
- The therapist will respond with context from past sessions
- Type `exit`, `quit`, or `end` to finish the session
- Press `Ctrl+C` to interrupt and save

### After a session

The system automatically:
- Extracts important facts and themes from the conversation
- Updates the client's profile and memory
- Saves the full session transcript
- Shows a summary of what was learned

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


## Testing

Run the comprehensive test suite:
```bash
python test.py
```

This tests all components:
- Storage (file I/O)
- Prompts (formatting)
- Memory Manager (GPT-4 and GPT-5)
- Therapist (GPT-4 and GPT-5)
- CLI

## Model Options

- **gpt-5**: Best reasoning and context usage (default)
- **gpt-5-mini**: Balanced speed and capability
- **gpt-5-nano**: Fastest, good for simple tasks

The system automatically uses the Responses API for better reasoning and chain of thought between conversation turns.

## How It Works

### During a Session
1. User sends message
2. System loads client profile (always)
3. LLM decides which past themes/sessions are relevant
4. Relevant context is loaded and formatted
5. Therapist responds with full context awareness
6. Repeat

### After a Session
1. LLM extracts important facts and themes from transcript
2. New facts are merged into profile (avoiding duplicates)
3. Themes are updated or added
4. Full session is saved with summary
5. Memory is ready for next session

## Data Storage

All client data is stored in JSON files:

```
data/clients/{client_id}/
├── profile.json       # Name, age, key facts, goals
├── themes.json        # Emotional patterns, progress markers
└── sessions/
    ├── session_001.json
    ├── session_002.json
    └── ...
```

You can inspect these files to see what the system learned!

## Architecture

```
main.py (CLI)
    ↓
therapist.py (Session Management)
    ↓
memory_manager.py (LLM Memory Operations)
    ↓
    ├── prompts.py (Formatting)
    └── storage.py (File I/O)
```

## Troubleshooting

### "OPENAI_API_KEY not found"
- Create `.env` file from `.env.example`
- Add your OpenAI API key

### Slow responses
- Normal - system makes multiple LLM calls
- Use `--model gpt-4o-mini` or `--model gpt-5-mini` for faster responses

### Memory not working
- Ensure using same client ID
- Check files are created in `data/clients/`
- Run `python test.py` to verify

### Model errors
- Ensure you have access to the models
- Check OpenAI API status
- Try a different model with `--model`

## Development

### Project Structure
- `main.py` - CLI interface
- `therapist.py` - Session management, conversation flow
- `memory_manager.py` - Memory extraction and retrieval
- `storage.py` - JSON file operations
- `prompts.py` - LLM prompts and formatting
- `test.py` - Comprehensive test suite

### Adding Features
1. Update relevant module (therapist, memory_manager, etc.)
2. Add tests to `test.py`
3. Update README if user-facing

## Performance

The system is optimized for speed with:
- `REASONING_EFFORT=minimal` - Fastest responses
- `VERBOSITY=low` - Concise outputs
- Efficient memory retrieval (only loads relevant context)

Typical response times:
- First message: 2-3 seconds
- Follow-up messages: 1-2 seconds
- Memory extraction: 2-3 seconds (happens after session ends)

## License

MIT License - See TASK.md for project requirements.
