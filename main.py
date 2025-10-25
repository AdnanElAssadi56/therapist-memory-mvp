"""
AI Therapist CLI - Interactive therapy sessions with memory.
"""

import os
import sys
import argparse
from dotenv import load_dotenv
from openai import OpenAI
from therapist import Therapist
import storage

# Load environment variables
load_dotenv()


def print_header():
    """Print welcome header."""
    print("\n" + "=" * 70)
    print("AI THERAPIST - Memory-Aware Therapy Sessions")
    print("=" * 70)
    print("\nThis is a safe space to share your thoughts and feelings.")
    print("Type 'exit' or 'quit' to end the session.\n")


def print_separator():
    """Print a visual separator."""
    print("-" * 70)


def get_client_id():
    """Get or create client ID."""
    print("\n👤 Client Identification")
    print_separator()
    
    # Check for existing clients
    data_dir = storage.DATA_DIR
    if data_dir.exists():
        existing_clients = [d.name for d in data_dir.iterdir() if d.is_dir()]
        if existing_clients:
            print("\nExisting clients:")
            for i, client in enumerate(existing_clients, 1):
                # Load profile to show name if available
                profile = storage.load_profile(client)
                name = profile.get("basic_info", {}).get("name", "Unknown")
                sessions = storage.list_sessions(client)
                print(f"  {i}. {client} ({name}) - {len(sessions)} session(s)")
    
    print("\nEnter client ID (or press Enter to create new):")
    client_id = input("Client ID: ").strip()
    
    if not client_id:
        # Generate new client ID
        import uuid
        client_id = f"client_{uuid.uuid4().hex[:8]}"
        print(f"\n✅ Created new client: {client_id}")
    else:
        # Check if returning client
        profile = storage.load_profile(client_id)
        if profile.get("key_facts"):
            name = profile.get("basic_info", {}).get("name", "")
            if name:
                print(f"\n✅ Welcome back, {name}!")
            else:
                print(f"\n✅ Continuing with client: {client_id}")
        else:
            print(f"\n✅ Starting new client: {client_id}")
    
    return client_id


def run_session(therapist: Therapist, client_id: str):
    """Run an interactive therapy session."""
    
    # Start session
    print("\n" + "=" * 70)
    print("SESSION STARTED")
    print("=" * 70)
    
    greeting = therapist.start_session()
    print(f"\n🤖 Therapist: {greeting}\n")
    
    # Conversation loop
    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()
            
            # Check for exit commands
            if user_input.lower() in ['exit', 'quit', 'end']:
                print("\n📝 Ending session...")
                break
            
            # Skip empty input
            if not user_input:
                continue
            
            # Get therapist response
            print("\n🤖 Therapist: ", end="", flush=True)
            response = therapist.send_message(user_input)
            print(response + "\n")
            
        except KeyboardInterrupt:
            print("\n\n⚠️  Session interrupted. Saving progress...")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Please try again or type 'exit' to end session.\n")
    
    # End session and save
    try:
        summary = therapist.end_session()
        
        print("\n" + "=" * 70)
        print("SESSION ENDED")
        print("=" * 70)
        
        print(f"\n📊 Session Summary:")
        print(f"   - Session ID: {summary['session_id']}")
        print(f"   - Messages exchanged: {summary['message_count']}")
        print(f"   - New facts learned: {summary['facts_learned']}")
        print(f"   - Themes identified: {summary['themes_identified']}")
        
        if summary.get('summary'):
            print(f"\n   Summary: {summary['summary']}")
        
        # Show where data is saved
        print(f"\n💾 Session saved to: data/clients/{client_id}/")
        
        # Show total stats
        profile = storage.load_profile(client_id)
        themes = storage.load_themes(client_id)
        sessions = storage.list_sessions(client_id)
        
        print(f"\n📈 Overall Progress:")
        print(f"   - Total sessions: {len(sessions)}")
        print(f"   - Total facts: {len(profile.get('key_facts', []))}")
        print(f"   - Total themes: {len(themes.get('recurring_themes', []))}")
        
    except Exception as e:
        print(f"\n❌ Error saving session: {e}")
        print("Your conversation may not have been saved.")


def main():
    """Main entry point."""
    
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="AI Therapist - Memory-aware therapy sessions"
    )
    parser.add_argument(
        "--client-id",
        type=str,
        help="Client ID to continue with (optional)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Model to use (default: gpt-5)"
    )
    parser.add_argument(
        "--memory-model",
        type=str,
        default=None,
        help="Model for memory operations (default: gpt-5-mini)"
    )
    args = parser.parse_args()
    
    # Print header
    print_header()
    
    # Check API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found in .env file")
        print("\nPlease create a .env file with your OpenAI API key:")
        print("  OPENAI_API_KEY=your_api_key_here")
        sys.exit(1)
    
    # Get client ID
    if args.client_id:
        client_id = args.client_id
        print(f"\n✅ Using client ID: {client_id}")
    else:
        client_id = get_client_id()
    
    # Initialize OpenAI client
    try:
        openai_client = OpenAI(api_key=api_key)
        print(f"\n✅ Connected to OpenAI (model: {args.model})")
    except Exception as e:
        print(f"\n❌ Error connecting to OpenAI: {e}")
        sys.exit(1)
    
    # Initialize therapist
    try:
        therapist = Therapist(
            client_id, 
            openai_client, 
            model=args.model,
            memory_model=args.memory_model
        )
        
        print(f"   Therapist model: {therapist.model}")
        print(f"   Memory model: {therapist.memory_manager.model}")
            
    except Exception as e:
        print(f"\n❌ Error initializing therapist: {e}")
        sys.exit(1)
    
    # Run session
    try:
        run_session(therapist, client_id)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    
    # Goodbye message
    print("\n" + "=" * 70)
    print("Thank you for using AI Therapist.")
    print("Take care of yourself. 💙")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
