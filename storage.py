"""
Storage module for handling JSON file I/O operations.
Manages client profiles, themes, and session data.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional


# Base data directory
DATA_DIR = Path("data/clients")


def ensure_client_directory(client_id: str) -> Path:
    """
    Create data/clients/{client_id}/ structure if it doesn't exist.
    
    Args:
        client_id: Unique identifier for the client
        
    Returns:
        Path to the client directory
    """
    client_path = DATA_DIR / client_id
    client_path.mkdir(parents=True, exist_ok=True)
    
    # Create sessions subdirectory
    sessions_path = client_path / "sessions"
    sessions_path.mkdir(exist_ok=True)
    
    return client_path


def load_profile(client_id: str) -> dict:
    """
    Load profile.json for a client.
    
    Args:
        client_id: Unique identifier for the client
        
    Returns:
        Profile data dict, or empty template if file doesn't exist
    """
    ensure_client_directory(client_id)
    profile_path = DATA_DIR / client_id / "profile.json"
    
    if profile_path.exists():
        try:
            with open(profile_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading profile: {e}")
            return _get_empty_profile_template(client_id)
    else:
        return _get_empty_profile_template(client_id)


def save_profile(client_id: str, profile_data: dict) -> None:
    """
    Save profile.json for a client.
    
    Args:
        client_id: Unique identifier for the client
        profile_data: Profile data to save
    """
    ensure_client_directory(client_id)
    profile_path = DATA_DIR / client_id / "profile.json"
    
    # Update timestamp
    profile_data["last_updated"] = datetime.now().isoformat()
    
    try:
        with open(profile_path, 'w', encoding='utf-8') as f:
            json.dump(profile_data, f, indent=2, ensure_ascii=False)
    except IOError as e:
        print(f"Error saving profile: {e}")


def load_themes(client_id: str) -> dict:
    """
    Load themes.json for a client.
    
    Args:
        client_id: Unique identifier for the client
        
    Returns:
        Themes data dict, or empty template if file doesn't exist
    """
    ensure_client_directory(client_id)
    themes_path = DATA_DIR / client_id / "themes.json"
    
    if themes_path.exists():
        try:
            with open(themes_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading themes: {e}")
            return _get_empty_themes_template()
    else:
        return _get_empty_themes_template()


def save_themes(client_id: str, themes_data: dict) -> None:
    """
    Save themes.json for a client.
    
    Args:
        client_id: Unique identifier for the client
        themes_data: Themes data to save
    """
    ensure_client_directory(client_id)
    themes_path = DATA_DIR / client_id / "themes.json"
    
    try:
        with open(themes_path, 'w', encoding='utf-8') as f:
            json.dump(themes_data, f, indent=2, ensure_ascii=False)
    except IOError as e:
        print(f"Error saving themes: {e}")


def save_session(client_id: str, session_data: dict) -> str:
    """
    Save a new session file with auto-generated session ID.
    
    Args:
        client_id: Unique identifier for the client
        session_data: Session data to save
        
    Returns:
        The generated session_id (e.g., "session_001")
    """
    ensure_client_directory(client_id)
    
    # Get next session number
    next_num = get_latest_session_number(client_id) + 1
    session_id = f"session_{next_num:03d}"
    
    # Add session_id and date to data
    session_data["session_id"] = session_id
    session_data["date"] = datetime.now().isoformat()
    
    # Save to file
    session_path = DATA_DIR / client_id / "sessions" / f"{session_id}.json"
    
    try:
        with open(session_path, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
        return session_id
    except IOError as e:
        print(f"Error saving session: {e}")
        return session_id


def load_session(client_id: str, session_id: str) -> Optional[dict]:
    """
    Load a specific session by ID.
    
    Args:
        client_id: Unique identifier for the client
        session_id: Session identifier (e.g., "session_001")
        
    Returns:
        Session data dict, or None if not found
    """
    session_path = DATA_DIR / client_id / "sessions" / f"{session_id}.json"
    
    if session_path.exists():
        try:
            with open(session_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading session {session_id}: {e}")
            return None
    else:
        return None


def list_sessions(client_id: str) -> list[str]:
    """
    Return list of all session IDs for a client, sorted chronologically.
    
    Args:
        client_id: Unique identifier for the client
        
    Returns:
        List of session IDs (e.g., ["session_001", "session_002"])
    """
    sessions_path = DATA_DIR / client_id / "sessions"
    
    if not sessions_path.exists():
        return []
    
    # Get all .json files and extract session IDs
    session_files = sorted(sessions_path.glob("session_*.json"))
    return [f.stem for f in session_files]


def get_latest_session_number(client_id: str) -> int:
    """
    Get the highest session number for a client.
    
    Args:
        client_id: Unique identifier for the client
        
    Returns:
        Latest session number (0 if no sessions exist)
    """
    sessions = list_sessions(client_id)
    
    if not sessions:
        return 0
    
    # Extract number from last session_id (e.g., "session_003" -> 3)
    last_session = sessions[-1]
    try:
        return int(last_session.split("_")[1])
    except (IndexError, ValueError):
        return 0


# Template functions

def _get_empty_profile_template(client_id: str) -> dict:
    """Return empty profile template."""
    return {
        "client_id": client_id,
        "basic_info": {},
        "key_facts": [],
        "current_goals": [],
        "created_at": datetime.now().isoformat(),
        "last_updated": datetime.now().isoformat()
    }


def _get_empty_themes_template() -> dict:
    """Return empty themes template."""
    return {
        "recurring_themes": [],
        "progress_markers": []
    }
