"""
Build 1: Session Store
========================
Save and resume conversations on disk. Load AGENTS.md into the system prompt.

Tasks:
  1. create_session() -> session_id
  2. save_session(session_id, messages, title?)
  3. load_session(session_id) -> {id, title, messages, ...}
  4. list_sessions() -> [{id, title, updated_at}, ...]
  5. build_system_prompt() -> base + AGENTS.md contents

Run twice: save a session in run 1, load it in run 2 and confirm messages restored.
"""

import json
import uuid
import os
from datetime import datetime, timezone
import nanoid

SESSIONS_DIR = ".agent/sessions"
BASE_PROMPT = "You are Research Desk, a helpful research assistant."

def create_session() -> str:
    """Initiates a new, empty session and saves it to disk."""
    os.makedirs(SESSIONS_DIR, exist_ok=True)
    
    session_id = nanoid.generate(size=8)
    new_session = {
        "id": session_id,
        "title": "Untitled",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "messages": [
            {"role": "system", "content": BASE_PROMPT}
        ]
    }
    
    file_path = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    with open(file_path, "w") as f:
        json.dump(new_session, f, indent=2)
        
    return session_id

def save_session(session_id: str, messages: list, title: str = "Untitled") -> None:
    """Updates the session file with new messages and an updated timestamp."""
    file_path = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    

    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            data = json.load(f)
    else:
       
        data = {"created_at": datetime.now(timezone.utc).isoformat()}
  

    data.update({
        "id": session_id,
        "title": title,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "messages": messages
    })
    
    # 3. Write (overwrite) the file
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)

def load_session(session_id: str) -> dict:
    """Load and return session dict including messages list."""
    file_path = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return json.load(f)
    return {}  


def list_sessions() -> list[dict]:
    """Return sessions sorted by updated_at descending."""
    sessions = []
    if not os.path.exists(SESSIONS_DIR):
        return []

    for filename in os.listdir(SESSIONS_DIR):
        if filename.endswith(".json"):
            file_path = os.path.join(SESSIONS_DIR, filename)
            with open(file_path, "r") as f:
                data = json.load(f)
                sessions.append({
                    "id": data.get("id"),
                    "title": data.get("title"),
                    "updated_at": data.get("updated_at")
                })
    
   
    return sorted(sessions, key=lambda x: x["updated_at"] or "", reverse=True)

def build_system_prompt() -> str:
    """Combine base prompt with AGENTS.md contents if available."""
    # Define the potential paths inside the function if you don't have a constant
    paths = ("AGENTS.md", ".agent/AGENTS.md")
    agents_content = ""
    
    for path in paths:
        if os.path.exists(path):
            with open(path, "r") as f:
                agents_content = f.read()
            break
    
    return f"{BASE_PROMPT}\n\n{agents_content}"


if __name__ == "__main__":
    sid = create_session()
    messages = [
        {"role": "system", "content": build_system_prompt()},
        {"role": "user", "content": "What is a surface code?"},
        {"role": "assistant", "content": "A surface code is a type of quantum error correcting code."},
    ]
    save_session(sid, messages, title="Quantum error correction\n")
    print(f"Saved session: {sid}\n")
    print(f"All sessions: {list_sessions()}\n")
    print(f"Loaded: {load_session(sid)['title']}\m") 