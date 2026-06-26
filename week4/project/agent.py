import os
import sys
import json
import nanoid
from datetime import datetime, timezone
from openai import OpenAI
from dotenv import load_dotenv

# --- Tool Imports ---
# Assuming you have placed the new tools in the tools/ directory as outlined in the spec
from tools.files import read_file, write_file, edit_file, list_files
from tools.exec import run_command
from tools.plan import add_todos, get_todos, mark_todo
from tools.search import grep, list_definitions
from tools.schema import TOOLS

# --- Setup ---
load_dotenv()

WORKSPACE_ROOT = os.path.abspath(os.environ.get("WORKSPACE_ROOT", "."))
MAX_ITERATIONS = 20  # Increased for multi-step codebase tasks
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
    """Load and return session dict including messages list."""
    file_path = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

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
        
        # True LLM Auto-Title
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
        """The main thinking loop for the LLM with Todo termination enforcement."""
        for _ in range(MAX_ITERATIONS):
            response = client.chat.completions.create(
                model=MODEL,
                messages=self.messages,
                tools=TOOLS,
                max_tokens=1000
            )
            
            msg = response.choices[0].message
            self.messages.append(msg.model_dump())

            # Loop Termination Logic: Check tools AND todo list
            if not msg.tool_calls:
                # Retrieve the current state of the agent's plan
                try:
                    todo_data = get_todos()
                    todos = todo_data.get("todos", [])
                    incomplete = [t for t in todos if t.get("status") in ("pending", "in_progress", "error")]
                    
                    if incomplete:
                        # Push back against premature stopping
                        nudge = (
                            "System: Your todo list still has pending, in_progress, or error items. "
                            "You must continue working through your plan, verify your changes with commands, "
                            "and update the list statuses. If you are genuinely blocked, mark the item as 'blocked' with a remark."
                        )
                        self.messages.append({"role": "user", "content": nudge})
                        save_session(self.session_id, self.messages, self.title)
                        continue # Force the loop to run again
                except Exception as e:
                    # Failsafe in case todo file is corrupted or not initialized yet
                    pass 
                
                return msg.content or ""
            
            for tool_call in msg.tool_calls:
                self._emit("tool_call", name=tool_call.function.name)
                result_json = self.dispatch(tool_call)
                
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result_json
                })
                
                # Mid-turn session flush
                save_session(self.session_id, self.messages, self.title)
                
        return "Error: Maximum iterations reached without resolving the task or completing the todo list."

    def dispatch(self, tool_call) -> str:
        """Map the LLM's requested function to actual Python code."""
        name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)
        
        # Updated tool map for Code Scout
        tool_map = {
            "read_file": read_file,
            "write_file": write_file,
            "edit_file": edit_file,
            "list_files": list_files,
            "run_command": run_command,
            "add_todos": add_todos,
            "get_todos": get_todos,
            "mark_todo": mark_todo,
            "grep": grep,
            "list_definitions": list_definitions
        }
        
        if name in tool_map:
            try:
                result_dict = tool_map[name](**args)
                return json.dumps(result_dict)
            except Exception as e:
                return json.dumps({"error": f"Tool execution failed: {str(e)}"})
                
        return json.dumps({"error": f"Tool '{name}' is not recognized."})

    def _emit(self, event: str, **data) -> None:
        pass


class REPLAgent(Agent):
    """Terminal REPL + one-shot CLI."""

    def run(self) -> None:
        print(f"Code Scout [Session: {self.session_id}] — Type '/quit' to exit")
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

            if user_input == "/sessions":
                print("\nPast Sessions:")
                if os.path.exists(SESSIONS_DIR):
                    files = os.listdir(SESSIONS_DIR)
                    for f in files:
                        if f.endswith(".json"):
                            sid = f.replace(".json", "")
                            session_data = load_session(sid)
                            title = session_data.get("title", "Untitled")
                            print(f" - {sid} : {title}")
                continue

            if user_input.startswith("/resume"):
                parts = user_input.split(maxsplit=1)
                if len(parts) < 2:
                    print("\n[Error: Please provide a session ID. Example: /resume abc123xyz]")
                    continue
                    
                target_id = parts[1].strip()
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
                
            response = self.chat(user_input)
            print(f"\nAgent: {response}\n")


# --- System Prompt Setup ---

def build_system_prompt() -> str:
    """Combine base instructions with dynamic context from AGENTS.md."""
    base_prompt = (
        "You are Code Scout, an autonomous software engineering agent. "
        "You have full access to the local codebase. You must create and manage a todo list "
        "to track your plan. You must verify code changes by running tests or linters before marking tasks complete."
    )
    agents_content = ""
    
    if os.path.exists("AGENTS.md"):
        with open("AGENTS.md", "r", encoding="utf-8") as f:
            agents_content = f.read()
            
    return f"{base_prompt}\n\n{agents_content}".strip()


def main():
    if len(sys.argv) > 1:
        # Check if the user is explicitly passing a session to resume
        if sys.argv[1] == "--session" and len(sys.argv) > 3:
            session_id = sys.argv[2]
            prompt = " ".join(sys.argv[3:])
            agent = REPLAgent(session_id=session_id)
            print(f"\nResuming session '{session_id}' for one-shot command: '{prompt}'")
            print(agent.run_once(prompt))
        elif sys.argv[1] == "--tui":
            from tui import TUIAgent
            resume_id = sys.argv[2] if len(sys.argv) > 2 else None
            app = TUIAgent(session_id=resume_id)
            app.run()
        else:
            prompt = " ".join(sys.argv[1:])
            agent = REPLAgent()
            print(f"\nRunning one-shot command: '{prompt}'")
            print(agent.run_once(prompt))
    else:
        agent = REPLAgent()
        agent.run()

if __name__ == "__main__":
    main()