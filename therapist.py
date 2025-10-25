"""
Therapist - Manages therapy sessions and conversation flow.
"""

import os
from datetime import datetime
from openai import OpenAI
from memory_manager import MemoryManager
import storage
import prompts


class Therapist:
    """Manages therapy sessions with memory-aware conversations."""
    
    def __init__(self, client_id: str, openai_client: OpenAI, model: str = None, memory_model: str = None):
        """
        Initialize therapist.
        
        Args:
            client_id: Unique identifier for the client
            openai_client: Initialized OpenAI client
            model: Model for therapist responses (defaults to gpt-5)
            memory_model: Model for memory operations (defaults to gpt-5-mini)
        """
        self.client_id = client_id
        self.client = openai_client
        self.model = model or os.getenv("THERAPIST_MODEL", "gpt-5")
        self.memory_manager = MemoryManager(client_id, openai_client, memory_model)
        self.reasoning_effort = os.getenv("REASONING_EFFORT", "minimal")
        self.verbosity = os.getenv("VERBOSITY", "medium")
        
        self.current_session = {
            "transcript": [],
            "started_at": None,
            "previous_response_id": None
        }
    
    def start_session(self) -> str:
        """Start a new therapy session."""
        self.current_session = {
            "transcript": [],
            "started_at": datetime.now().isoformat()
        }
        
        profile = storage.load_profile(self.client_id)
        is_new_client = not profile.get("key_facts") and not profile.get("basic_info")
        
        greeting = self._generate_new_client_greeting() if is_new_client else self._generate_returning_greeting()
        
        self.current_session["transcript"].append({
            "role": "assistant",
            "content": greeting
        })
        
        return greeting
    
    def send_message(self, user_message: str) -> str:
        """Process user message and generate therapist response."""
        if not self.current_session.get("started_at"):
            raise RuntimeError("Session not started. Call start_session() first.")
        
        self.current_session["transcript"].append({
            "role": "user",
            "content": user_message
        })
        
        try:
            context = self.memory_manager.get_relevant_context(user_message)
            formatted_context = self.memory_manager.format_context_for_therapist(context)
        except Exception as e:
            print(f"Warning: Could not retrieve context: {e}")
            profile = storage.load_profile(self.client_id)
            formatted_context = prompts.format_context_for_therapist(profile, {}, [])
        
        system_prompt = f"{prompts.THERAPIST_SYSTEM_PROMPT}\n\n{formatted_context}"
        
        # Build conversation text for Responses API
        recent_transcript = self.current_session["transcript"][-20:]
        conversation_text = self._format_messages(system_prompt, recent_transcript)
        
        try:
            # Build API call parameters
            api_params = {
                "model": self.model,
                "input": conversation_text,
                "max_output_tokens": 500
            }
            
            # Only add reasoning/verbosity for gpt-5 models
            if self.model.startswith("gpt-5"):
                api_params["reasoning"] = {"effort": self.reasoning_effort}
                api_params["text"] = {"verbosity": self.verbosity}
            
            response = self.client.responses.create(**api_params)
            therapist_response = response.output_text
            
            if not therapist_response:
                therapist_response = "I'm listening. Please tell me more."
            
        except Exception as e:
            print(f"Error generating response: {e}")
            try:
                api_params = {
                    "model": self.model,
                    "input": f"{prompts.THERAPIST_SYSTEM_PROMPT}\n\nUser: {user_message}"
                }
                
                if self.model.startswith("gpt-5"):
                    api_params["reasoning"] = {"effort": "minimal"}
                    api_params["text"] = {"verbosity": "low"}
                
                response = self.client.responses.create(**api_params)
                therapist_response = response.output_text
            except Exception as e2:
                print(f"Retry failed: {e2}")
                therapist_response = "I'm having trouble processing that right now. Could you tell me more?"
        
        self.current_session["transcript"].append({
            "role": "assistant",
            "content": therapist_response
        })
        
        return therapist_response
    
    def end_session(self) -> dict:
        """End the current session and save memories."""
        if not self.current_session.get("started_at"):
            raise RuntimeError("No active session to end.")
        
        if len(self.current_session["transcript"]) == 0:
            raise RuntimeError("Cannot end empty session.")
        
        try:
            extracted = self.memory_manager.extract_memories(
                self.current_session["transcript"]
            )
        except Exception as e:
            print(f"Error extracting memories: {e}")
            extracted = {
                "new_facts": [],
                "themes": [],
                "session_summary": "Session completed",
                "next_session_focus": ""
            }
        
        try:
            self.memory_manager.update_memories(extracted)
        except Exception as e:
            print(f"Error updating memories: {e}")
        
        session_data = {
            "transcript": self.current_session["transcript"],
            "summary": extracted.get("session_summary", ""),
            "extracted_facts": extracted.get("new_facts", []),
            "themes_discussed": [t.get("name", "") for t in extracted.get("themes", [])],
            "next_session_focus": extracted.get("next_session_focus", ""),
            "started_at": self.current_session["started_at"],
            "ended_at": datetime.now().isoformat()
        }
        
        session_id = storage.save_session(self.client_id, session_data)
        
        summary = {
            "session_id": session_id,
            "summary": extracted.get("session_summary", ""),
            "facts_learned": len(extracted.get("new_facts", [])),
            "themes_identified": len(extracted.get("themes", [])),
            "message_count": len(self.current_session["transcript"])
        }
        
        self.current_session = {
            "transcript": [],
            "started_at": None
        }
        
        return summary
    
    def get_session_stats(self) -> dict:
        """Get stats about current session."""
        user_messages = [m for m in self.current_session["transcript"] if m["role"] == "user"]
        assistant_messages = [m for m in self.current_session["transcript"] if m["role"] == "assistant"]
        
        return {
            "is_active": self.current_session.get("started_at") is not None,
            "message_count": len(self.current_session["transcript"]),
            "user_messages": len(user_messages),
            "assistant_messages": len(assistant_messages),
            "started_at": self.current_session.get("started_at")
        }
    
    def _format_messages(self, system_prompt: str, messages: list[dict]) -> str:
        """Format messages for LLM input."""
        formatted_parts = [f"System: {system_prompt}"]
        
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            
            if role == "user":
                formatted_parts.append(f"User: {content}")
            elif role == "assistant":
                formatted_parts.append(f"Assistant: {content}")
        
        return "\n\n".join(formatted_parts)
    
    def _generate_new_client_greeting(self) -> str:
        """Generate greeting for new client."""
        return ("Hello, I'm here to listen and support you. This is a safe space where you can "
                "share whatever is on your mind. How are you feeling today?")
    
    def _generate_returning_greeting(self) -> str:
        """Generate personalized greeting for returning client."""
        try:
            profile = storage.load_profile(self.client_id)
            sessions = storage.list_sessions(self.client_id)
            
            context_parts = []
            
            if profile.get("basic_info", {}).get("name"):
                context_parts.append(f"Client name: {profile['basic_info']['name']}")
            
            if sessions:
                last_session = storage.load_session(self.client_id, sessions[-1])
                if last_session and last_session.get("next_session_focus"):
                    context_parts.append(f"Last session we discussed: {last_session.get('summary', 'previous topics')}")
                    context_parts.append(f"Follow-up focus: {last_session['next_session_focus']}")
            
            if not context_parts:
                return "Welcome back. How have you been since we last spoke?"
            
            context_str = "\n".join(context_parts)
            
            prompt = f"""Generate a warm, brief greeting for a returning therapy client.

Context:
{context_str}

Keep it natural, empathetic, and brief (1-2 sentences). You can reference what we discussed last time if relevant, but keep it light. Don't ask multiple questions."""
            
            api_params = {
                "model": self.model,
                "input": f"You are an empathetic therapist greeting a returning client.\n\n{prompt}",
                "max_output_tokens": 100
            }
            
            if self.model.startswith("gpt-5"):
                api_params["reasoning"] = {"effort": "minimal"}
                api_params["text"] = {"verbosity": "low"}
            
            response = self.client.responses.create(**api_params)
            return response.output_text
            
        except Exception as e:
            print(f"Error generating returning greeting: {e}")
            return "Welcome back. How have you been since we last spoke?"
