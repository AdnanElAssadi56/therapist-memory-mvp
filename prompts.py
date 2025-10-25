"""
Prompts and context formatting for the AI therapist and memory system.
"""

# System prompt for the therapist
THERAPIST_SYSTEM_PROMPT = """You are an empathetic and professional AI therapist. Your role is to:

- Listen actively and validate the client's feelings
- Ask thoughtful, open-ended questions to explore their experiences
- Help clients identify patterns and insights
- Maintain appropriate therapeutic boundaries
- Be warm, non-judgmental, and supportive
- Focus on the client's emotional well-being and growth

IMPORTANT: You have access to the client's profile, past sessions, and recurring themes below. Use this information to:
- Personalize your responses (use their name when appropriate)
- Reference relevant past discussions or themes
- Show continuity and that you remember what they've shared
- Connect current topics to patterns you've observed

Remember: You are having a conversation, not giving advice. Help clients explore their own thoughts and feelings."""


# Prompt for extracting memories after a session
MEMORY_EXTRACTION_PROMPT = """You are a therapist reviewing a session transcript. Extract the following information to update the client's memory:

TRANSCRIPT:
{transcript}

Extract and return as JSON with this exact structure:
{{
  "new_facts": [
    "List any new factual information about the client (name, age, job, relationships, life events, etc.)"
  ],
  "updated_facts": [
    "List any updates to existing facts (e.g., 'Changed jobs from X to Y')"
  ],
  "themes": [
    {{
      "name": "short_identifier_for_theme",
      "description": "Brief description of the emotional or behavioral pattern",
      "intensity": "high|medium|low",
      "notes": "Specific details or triggers related to this theme"
    }}
  ],
  "session_summary": "2-3 sentence summary of what was discussed and any breakthroughs",
  "important_moments": [
    "List any particularly significant moments (breakthroughs, emotional releases, insights)"
  ],
  "progress_markers": [
    "List any signs of progress or positive changes"
  ],
  "next_session_focus": "What should be followed up on or explored further next time"
}}

Focus on what would be therapeutically important to remember. Be concise but capture the essence."""


# Prompt for deciding which memories to retrieve
MEMORY_RETRIEVAL_PROMPT = """You are helping decide which past memories are relevant for the current therapy conversation.

CURRENT USER MESSAGE:
{current_message}

CLIENT PROFILE:
{profile_summary}

AVAILABLE THEMES:
{available_themes}

AVAILABLE PAST SESSIONS:
{available_sessions}

Decide which themes and sessions would be most relevant to recall for this conversation. Return as JSON:
{{
  "relevant_themes": ["list of theme names that are relevant"],
  "relevant_sessions": ["list of session IDs that should be recalled"],
  "reasoning": "Brief explanation of why these are relevant"
}}

Only include what's truly relevant. It's okay to return empty lists if nothing from the past is particularly relevant to the current message."""


def format_context_for_therapist(profile: dict, themes: dict, recent_sessions: list[dict]) -> str:
    """
    Format the memory context to include in the therapist's system prompt.
    
    Args:
        profile: Client profile data
        themes: Client themes data
        recent_sessions: List of recent session summaries
        
    Returns:
        Formatted context string
    """
    context_parts = []
    
    # Add profile information
    context_parts.append("=== CLIENT PROFILE ===")
    
    if profile.get("basic_info"):
        info_lines = [f"- {k}: {v}" for k, v in profile["basic_info"].items()]
        context_parts.append("\n".join(info_lines))
    
    if profile.get("key_facts"):
        context_parts.append("\nKey Facts:")
        for fact in profile["key_facts"]:
            context_parts.append(f"• {fact}")
    
    if profile.get("current_goals"):
        context_parts.append("\nCurrent Goals:")
        for goal in profile["current_goals"]:
            context_parts.append(f"• {goal}")
    
    # Add themes
    if themes.get("recurring_themes"):
        context_parts.append("\n=== RECURRING THEMES ===")
        for theme in themes["recurring_themes"]:
            context_parts.append(f"\n{theme.get('name', 'Unknown').replace('_', ' ').title()}")
            context_parts.append(f"  Intensity: {theme.get('intensity', 'unknown')}")
            if theme.get("notes"):
                context_parts.append(f"  Notes: {theme['notes']}")
    
    # Add progress markers
    if themes.get("progress_markers"):
        context_parts.append("\n=== PROGRESS MARKERS ===")
        for marker in themes["progress_markers"]:
            date = marker.get("date", "Unknown date")
            milestone = marker.get("milestone", "")
            context_parts.append(f"• [{date}] {milestone}")
    
    # Add recent session summaries
    if recent_sessions:
        context_parts.append("\n=== RECENT SESSIONS ===")
        for session in recent_sessions:
            session_id = session.get("session_id", "Unknown")
            date = session.get("date", "Unknown date")[:10]  # Just the date part
            summary = session.get("summary", "No summary")
            context_parts.append(f"\n{session_id} ({date}):")
            context_parts.append(f"  {summary}")
    
    return "\n".join(context_parts)


def format_profile_summary(profile: dict) -> str:
    """
    Create a brief summary of the profile for memory retrieval decisions.
    
    Args:
        profile: Client profile data
        
    Returns:
        Brief profile summary
    """
    parts = []
    
    if profile.get("basic_info"):
        info_str = ", ".join([f"{k}: {v}" for k, v in profile["basic_info"].items()])
        parts.append(info_str)
    
    if profile.get("key_facts"):
        parts.append(f"Key facts: {'; '.join(profile['key_facts'][:3])}")  # First 3 facts
    
    return " | ".join(parts) if parts else "New client, no profile yet"


def format_available_themes(themes: dict) -> str:
    """
    Format themes list for memory retrieval prompt.
    
    Args:
        themes: Client themes data
        
    Returns:
        Formatted themes string
    """
    if not themes.get("recurring_themes"):
        return "No themes recorded yet"
    
    theme_lines = []
    for theme in themes["recurring_themes"]:
        name = theme.get("name", "unknown")
        desc = theme.get("description", "")
        theme_lines.append(f"- {name}: {desc}")
    
    return "\n".join(theme_lines)


def format_available_sessions(session_ids: list[str]) -> str:
    """
    Format session IDs list for memory retrieval prompt.
    
    Args:
        session_ids: List of session IDs
        
    Returns:
        Formatted sessions string
    """
    if not session_ids:
        return "No previous sessions"
    
    return ", ".join(session_ids)


def format_transcript_for_extraction(transcript: list[dict]) -> str:
    """
    Format conversation transcript for memory extraction.
    
    Args:
        transcript: List of message dicts with 'role' and 'content'
        
    Returns:
        Formatted transcript string
    """
    lines = []
    for msg in transcript:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        
        if role == "user":
            lines.append(f"Client: {content}")
        elif role == "assistant":
            lines.append(f"Therapist: {content}")
    
    return "\n\n".join(lines)
