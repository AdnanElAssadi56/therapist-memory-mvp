"""
Memory Manager - LLM-powered memory extraction and retrieval.
"""

import json
import os
from typing import Optional
from openai import OpenAI
import storage
import prompts


class MemoryManager:
    """Manages memory extraction, storage, and retrieval using LLM."""
    
    def __init__(self, client_id: str, openai_client: OpenAI, model: str = None):
        """
        Initialize memory manager.
        
        Args:
            client_id: Unique identifier for the client
            openai_client: Initialized OpenAI client
            model: Model to use (defaults to gpt-5-mini)
        """
        self.client_id = client_id
        self.client = openai_client
        self.model = model or os.getenv("MEMORY_MODEL", "gpt-5-mini")
        self.reasoning_effort = os.getenv("REASONING_EFFORT", "low")
        self.verbosity = os.getenv("VERBOSITY", "medium")
    
    def extract_memories(self, transcript: list[dict]) -> dict:
        """Extract memories from a session transcript."""
        transcript_str = prompts.format_transcript_for_extraction(transcript)
        prompt = prompts.MEMORY_EXTRACTION_PROMPT.format(transcript=transcript_str)
        
        try:
            extracted = self._call_llm_json(
                system_msg="You are a therapist reviewing a session to extract important information.",
                user_msg=prompt
            )
            return self._validate_extraction(extracted)
        except Exception as e:
            print(f"Error extracting memories: {e}")
            return self._get_empty_extraction()
    
    def update_memories(self, extracted_data: dict) -> None:
        """Update profile and themes with extracted data."""
        profile = storage.load_profile(self.client_id)
        themes = storage.load_themes(self.client_id)
        
        if extracted_data.get("new_facts"):
            profile["key_facts"] = self._merge_facts(
                profile.get("key_facts", []),
                extracted_data["new_facts"]
            )
        
        if extracted_data.get("basic_info"):
            profile["basic_info"].update(extracted_data["basic_info"])
        
        if extracted_data.get("themes"):
            themes["recurring_themes"] = self._merge_themes(
                themes.get("recurring_themes", []),
                extracted_data["themes"]
            )
        
        if extracted_data.get("progress_markers"):
            existing_markers = themes.get("progress_markers", [])
            for marker in extracted_data["progress_markers"]:
                if isinstance(marker, str):
                    marker = {"milestone": marker, "date": storage.datetime.now().isoformat()[:10]}
                existing_markers.append(marker)
            themes["progress_markers"] = existing_markers
        
        storage.save_profile(self.client_id, profile)
        storage.save_themes(self.client_id, themes)
    
    def get_relevant_context(self, current_message: str) -> dict:
        """Get relevant memory context for the current message."""
        profile = storage.load_profile(self.client_id)
        themes = storage.load_themes(self.client_id)
        session_ids = storage.list_sessions(self.client_id)
        
        context = {
            "profile": profile,
            "relevant_themes": [],
            "relevant_sessions": []
        }
        
        if not themes.get("recurring_themes") and not session_ids:
            return context
        
        try:
            profile_summary = prompts.format_profile_summary(profile)
            available_themes = prompts.format_available_themes(themes)
            available_sessions = prompts.format_available_sessions(session_ids)
            
            prompt = prompts.MEMORY_RETRIEVAL_PROMPT.format(
                current_message=current_message,
                profile_summary=profile_summary,
                available_themes=available_themes,
                available_sessions=available_sessions
            )
            
            retrieval = self._call_llm_json(
                system_msg="You decide which past memories are relevant for therapy conversations.",
                user_msg=prompt
            )
            
            relevant_theme_names = retrieval.get("relevant_themes", [])
            if relevant_theme_names:
                context["relevant_themes"] = [
                    theme for theme in themes.get("recurring_themes", [])
                    if theme.get("name") in relevant_theme_names
                ]
            
            relevant_session_ids = retrieval.get("relevant_sessions", [])
            if relevant_session_ids:
                context["relevant_sessions"] = [
                    storage.load_session(self.client_id, sid)
                    for sid in relevant_session_ids
                    if storage.load_session(self.client_id, sid) is not None
                ]
            
        except Exception as e:
            print(f"Error retrieving relevant context: {e}")
            if session_ids:
                recent_ids = session_ids[-2:]
                context["relevant_sessions"] = [
                    storage.load_session(self.client_id, sid)
                    for sid in recent_ids
                    if storage.load_session(self.client_id, sid) is not None
                ]
        
        return context
    
    def format_context_for_therapist(self, context: dict) -> str:
        """Format memory context for therapist system prompt."""
        profile = context.get("profile", {})
        relevant_themes = context.get("relevant_themes", [])
        relevant_sessions = context.get("relevant_sessions", [])
        
        themes_dict = {
            "recurring_themes": relevant_themes,
            "progress_markers": profile.get("progress_markers", [])
        }
        
        return prompts.format_context_for_therapist(
            profile=profile,
            themes=themes_dict,
            recent_sessions=relevant_sessions
        )
    
    def _call_llm_json(self, system_msg: str, user_msg: str) -> dict:
        """Call LLM with JSON mode using Responses API."""
        full_input = f"{system_msg}\n\n{user_msg}\n\nRespond with valid JSON only."
        
        api_params = {
            "model": self.model,
            "input": full_input
        }
        
        # Only add reasoning/verbosity for gpt-5 models
        if self.model.startswith("gpt-5"):
            api_params["reasoning"] = {"effort": self.reasoning_effort}
            api_params["text"] = {"verbosity": self.verbosity}
        
        response = self.client.responses.create(**api_params)
        return json.loads(response.output_text)
    
    def _merge_facts(self, existing_facts: list, new_facts: list) -> list:
        """Merge facts, avoiding duplicates."""
        merged = existing_facts.copy()
        
        for new_fact in new_facts:
            new_fact_lower = new_fact.lower()
            is_duplicate = any(
                new_fact_lower in existing.lower() or existing.lower() in new_fact_lower
                for existing in existing_facts
            )
            
            if not is_duplicate:
                merged.append(new_fact)
        
        return merged
    
    def _merge_themes(self, existing_themes: list, new_themes: list) -> list:
        """Merge themes, updating existing or adding new."""
        themes_dict = {theme["name"]: theme for theme in existing_themes}
        
        for new_theme in new_themes:
            theme_name = new_theme.get("name")
            if theme_name in themes_dict:
                themes_dict[theme_name].update(new_theme)
            else:
                themes_dict[theme_name] = new_theme
        
        return list(themes_dict.values())
    
    def _validate_extraction(self, extracted: dict) -> dict:
        """Validate and fill missing fields in extraction."""
        template = self._get_empty_extraction()
        
        for key in template:
            if key in extracted:
                template[key] = extracted[key]
        
        return template
    
    def _get_empty_extraction(self) -> dict:
        """Return empty extraction template."""
        return {
            "new_facts": [],
            "updated_facts": [],
            "themes": [],
            "session_summary": "",
            "important_moments": [],
            "progress_markers": [],
            "next_session_focus": ""
        }
