import os
import json
import nanoid
from datetime import datetime, timezone

SESSIONS_DIR = ".agent/sessions"

def build_system_prompt() -> str:
    base_prompt = (
        "You are Code Scout, an autonomous software engineering agent. "
        "You have access to a local codebase. Manage your plan targets accurately."
    )
    agents_content = ""
    if os.path.exists("AGENTS.md"):
        with open("AGENTS.md", "r", encoding="utf-8") as f:
            agents_content = f.read()
    return f"{base_prompt}\n\n{agents_content}".strip()

def create_session() -> str:
    os.makedirs(SESSIONS_DIR, exist_ok=True)
    session_id = nanoid.generate(size=8)
    
    new_session = {
        "id": session_id,
        "title": "Untitled",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "messages": [{"role": "system", "content": build_system_prompt()}]
    }
    
    file_path = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(new_session, f, indent=2)
        
    return session_id

def save_session(session_id: str, messages: list, title: str = "Untitled") -> None:
    if session_id == "temp_scout": 
        return  

    file_path = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {"created_at": datetime.now(timezone.utc).isoformat()}
        
    data.update({
        "id": session_id,
        "title": title,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "messages": messages
    })
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def load_session(session_id: str) -> dict:
    file_path = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def delete_session(session_id: str) -> bool:
    """Deletes a session file by its unique session ID."""
    file_path = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    if os.path.exists(file_path):
        os.remove(file_path)
        return True
    return False