import os
import sys
import json
import glob as glob_module
import nanoid
from datetime import datetime, timezone
from openai import OpenAI
from dotenv import load_dotenv

# --- New Tool Imports ---
from tools.web import web_search, web_fetch
from tools.papers import paper_search, read_paper
from tools.files import read_file, write_file, edit_file, list_files
from tools.schema import TOOLS



# --- Setup ---
load_dotenv()

WORKSPACE_ROOT = os.path.abspath(os.environ.get("WORKSPACE_ROOT", "."))
MAX_ITERATIONS = 10
MAX_READ_CHARS = 12_000
SESSIONS_DIR = ".agent/sessions"

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY"),
)

MODEL = "openrouter/owl-alpha"


# --- Session Management ---

def create_session() -> str:
    """Initiates a new, empty session and saves it to disk."""
    os.makedirs(SESSIONS_DIR, exist_ok=True)
    session_id = nanoid.generate(size=8)
    
    new_session = {
        "id": session_id,
        "title": "Untitled",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "messages": [
            {"role": "system", "content": build_system_prompt()}
        ]
    }
    
    file_path = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(new_session, f, indent=2)
        
    return session_id

def save_session(session_id: str, messages: list, title: str = "Untitled") -> None:
    """Updates the session file with new messages, dynamic title, and an updated timestamp."""
    file_path = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    
    # Load existing data to preserve the original 'created_at' timestamp
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {"created_at": datetime.now(timezone.utc).isoformat()}
        
    # Update the dictionary with the latest state
    data.update({
        "id": session_id,
        "title": title,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "messages": messages
    })
    
    # Write everything back to the JSON file
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def load_session(session_id: str) -> dict:
    """Load and return session dict including messages list."""
    file_path = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


# --- File System Tools ---

def resolve_path(path: str) -> str:
    """Ensure path is within WORKSPACE_ROOT and return absolute path."""
    full_path = os.path.normpath(os.path.join(WORKSPACE_ROOT, path))
    if not full_path.startswith(os.path.abspath(WORKSPACE_ROOT)):
        raise PermissionError(f"Access denied: {path} is outside the workspace.")
    return full_path


# --- Agent Class Hierarchy ---

class Agent:
    """Core agent: loop, tools, sessions. No UI."""

    def __init__(self, session_id=None):
        self.title = "Untitled"
        
        if session_id:
            self.session_id = session_id
            session_data = load_session(session_id)
            self.title = session_data.get("title", "Untitled") 
            self.messages = session_data.get("messages", [])
        else:
            self.session_id = create_session()
            self.messages = [{"role": "system", "content": build_system_prompt()}]



    def chat(self, user_message: str) -> str:
        """Process a single user message and return the final response."""
        self.messages.append({"role": "user", "content": user_message})
        
        final_response = self._run_loop()
        
        # --- NEW: True LLM Auto-Title ---
        if self.title == "Untitled":
            try:
                title_prompt = f"Summarize this exact request in 5 words or less. Output ONLY the summary: '{user_message}'"
                title_response = client.chat.completions.create(
                    model=MODEL,
                    messages=[{"role": "user", "content": title_prompt}],
                    max_tokens=15
                )
                self.title = title_response.choices[0].message.content.strip().replace('"', '')
            except Exception:
                self.title = user_message[:35] + "..."

        save_session(self.session_id, self.messages, self.title)
        return final_response
    


    def run_once(self, prompt: str) -> str:
        return self.chat(prompt)



    def _run_loop(self) -> str:
        """The main thinking loop for the LLM."""
        for _ in range(MAX_ITERATIONS):
            response = client.chat.completions.create(
                model=MODEL,
                messages=self.messages,
                tools=TOOLS,
                max_tokens=500
            )
            
            msg = response.choices[0].message
            self.messages.append(msg.model_dump(exclude_none=True))

            if not msg.tool_calls:
                return msg.content
            
            for tool_call in msg.tool_calls:
                self._emit("tool_call", name=tool_call.function.name)
                result_json = self.dispatch(tool_call)
                
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result_json
                })
                
        return "Error: Maximum iterations reached without resolving the task."

    def dispatch(self, tool_call) -> str:
        """Map the LLM's requested function to actual Python code."""
        name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)
        
        tool_map = {
            "read_file": read_file,
            "write_file": write_file,
            "edit_file": edit_file,
            "list_files": list_files,
            "web_search": web_search,
            "web_fetch": web_fetch,
            "paper_search": paper_search,
            "read_paper": read_paper
        }
        
        if name in tool_map:
            try:
                result_dict = tool_map[name](**args)
                return json.dumps(result_dict)
            except Exception as e:
                return json.dumps({"error": f"Tool execution failed: {str(e)}"})
                
        return json.dumps({"error": f"Tool '{name}' is not recognized."})

    def _emit(self, event: str, **data) -> None:
        """Override in REPLAgent/TUIAgent for tool logging."""
        pass


class REPLAgent(Agent):
    """Terminal REPL + one-shot CLI."""

    def run(self) -> None:
        print(f"Research Desk [Session: {self.session_id}] — Type '/quit' to exit")
        print("Type '/sessions' to view history, or '/resume <id>' to switch.")
        print("-" * 50)
        
        while True:
            try:
                user_input = input("\n> ").strip()
            except (EOFError, KeyboardInterrupt):
                break
                
            if not user_input or user_input in ("/quit", "/exit"):
                print("Goodbye!")
                break

            # --- BONUS CHALLENGE: /sessions ---
            if user_input == "/sessions":
                print("\nPast Sessions:")
                if os.path.exists(SESSIONS_DIR):
                    files = os.listdir(SESSIONS_DIR)
                    for f in files:
                        if f.endswith(".json"):
                            session_data = load_session(f.replace(".json", ""))
                            title = session_data.get("title", "Untitled")
                            print(f" - {f.replace('.json', '')} : {title}")
                continue

            # --- BONUS CHALLENGE: /resume <id> ---
            if user_input.startswith("/resume "):
                try:
                    target_id = user_input.split(" ")[1]
                except IndexError:
                    print("\n[Error: Please provide a session ID. Example: /resume abc123xyz]")
                    continue
                    
                file_path = os.path.join(SESSIONS_DIR, f"{target_id}.json")
                if os.path.exists(file_path):
                    self.session_id = target_id
                    session_data = load_session(target_id)
                    self.title = session_data.get("title", "Untitled")
                    self.messages = session_data.get("messages", [])
                    print(f"\n[Successfully resumed session: {target_id}]")
                else:
                    print(f"\n[Error: Session '{target_id}' not found]")
                continue
                
            # If it's not a command, send it to the AI
            response = self.chat(user_input)
            print(f"\nAgent: {response}\n")


# --- System Prompt Setup ---

def build_system_prompt() -> str:
    """Combine base instructions with dynamic context from AGENTS.md."""
    base_prompt = "You are Research Desk, a highly capable coding assistant. You have full access to the local file system, web search, and academic papers."
    agents_content = ""
    
    if os.path.exists("AGENTS.md"):
        with open("AGENTS.md", "r", encoding="utf-8") as f:
            agents_content = f.read()
            
    return f"{base_prompt}\n\n{agents_content}".strip()


def main():
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        
        if arg == "--tui":
            from tui import TUIAgent
            # Grab the ID from the terminal command
            resume_id = sys.argv[2] if len(sys.argv) > 2 else None
            
            # Pass it into the TUIAgent!
            app = TUIAgent(session_id=resume_id)
            app.run()
        else:
            # One-shot mode
            prompt = " ".join(sys.argv[1:])
            agent = REPLAgent()
            print(f"\nRunning one-shot command: '{prompt}'")
            print(agent.run_once(prompt))
    else:
        # Interactive mode
        agent = REPLAgent()
        agent.run()

if __name__ == "__main__":
    main()