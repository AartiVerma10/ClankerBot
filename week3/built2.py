"""
Build 2: Agent + REPLAgent
===========================
Agent = brain (loop, tools, sessions). REPLAgent = terminal UI.

Before running:
  mkdir -p notes

Tasks:
  1. Agent — chat(), run_once(), _run_loop(), dispatch(), _emit(), session I/O
  2. REPLAgent(Agent) — run() interactive loop
  3. resolve_path, read_file, write_file, list_files, edit_file
  4. main() — one-shot: python build2_agent_class.py "hello"

TUIAgent comes in the project (tui.py). No Textual imports here.
"""

import os
import sys
import json
import glob as glob_module
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

WORKSPACE_ROOT = os.path.abspath(os.environ.get("WORKSPACE_ROOT", "."))
MAX_ITERATIONS = 10
MAX_READ_CHARS = 12_000

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)
MODEL = "deepseek/deepseek-chat"



def resolve_path(path: str) -> str:
    """Ensure path is within WORKSPACE_ROOT and return absolute path."""
    
    full_path = os.path.normpath(os.path.join(WORKSPACE_ROOT, path))
    
    if not full_path.startswith(os.path.abspath(WORKSPACE_ROOT)):
        raise PermissionError(f"Access denied: {path} is outside the workspace.")
    return full_path

def read_file(path: str, start_line: int = 1, read_lines: int = 200) -> dict:
    """Read a specific range of lines from a file."""
    try:
        abs_path = resolve_path(path)
        with open(abs_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        
        start_idx = max(0, start_line - 1)
        end_idx = start_idx + read_lines
        
        content = "".join(lines[start_idx:end_idx])
        
       
        if len(content) > MAX_READ_CHARS:
            content = content[:MAX_READ_CHARS] + "\n...[truncated]"
            
        return {"content": content, "total_lines": len(lines)}
    except Exception as e:
        return {"error": str(e)}

def write_file(path: str, content: str) -> dict:
    """Write content to a file, creating directories if needed."""
    try:
        abs_path = resolve_path(path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return {"content": f"Successfully wrote to {path}"}
    except Exception as e:
        return {"error": str(e)}  

def edit_file(
    path: str,
    operation: str,
    start_line: int,
    end_line: int | None = None,
    content: str | None = None,
) -> dict:
    """Surgically edit a file: operation can be 'replace' or 'delete'."""
    try:
        abs_path = resolve_path(path)
        with open(abs_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        
        start_idx = max(0, start_line - 1)
        # If end_line is None, just target the single start_line
        end_idx = end_line if end_line is not None else start_line

        if operation == "replace":
            new_lines = [line + "\n" for line in content.splitlines()]
            lines[start_idx:end_idx] = new_lines
        elif operation == "delete":
            del lines[start_idx:end_idx]
        else:
            return {"error": f"Unknown operation: {operation}"}

        with open(abs_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
            
        return {"content": f"Successfully performed {operation} on {path}"}
    except Exception as e:
        return {"error": str(e)}            


def list_files(path: str = ".", pattern: str = "*") -> dict:
    """List files in the workspace matching a glob pattern."""
    try:
        abs_path = resolve_path(path)
        search_path = os.path.join(abs_path, pattern)
        files = glob_module.glob(search_path, recursive=True)
        
        
        relative_files = [os.path.relpath(f, WORKSPACE_ROOT) for f in files]
        
        return {"files": relative_files}
    except Exception as e:
        return {"error": str(e)}

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file from the workspace",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "start_line": {"type": "integer"},
                    "read_lines": {"type": "integer"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"}
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": "Surgically edit a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "operation": {"type": "string", "enum": ["replace", "delete"]},
                    "start_line": {"type": "integer"},
                    "end_line": {"type": "integer"},
                    "content": {"type": "string"}
                },
                "required": ["path", "operation", "start_line"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files in workspace",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "pattern": {"type": "string"}
                }
            }
        }
    }
]


import nanoid
from datetime import datetime, timezone

SESSIONS_DIR = ".agent/sessions"

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
    
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)

def load_session(session_id: str) -> dict:
    """Load and return session dict including messages list."""
    file_path = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return json.load(f)
    return {}


class Agent:
    """Core agent: loop, tools, sessions. No UI."""

    def __init__(self, workspace: str = ".", session_id: str | None = None):
        self.workspace = os.path.abspath(workspace)
        
        if session_id:
            self.session_id = session_id
           
            session_data = load_session(session_id) 
            self.messages = session_data.get("messages", [])
        else:
           
            self.session_id = create_session() 
            self.messages = [{"role": "system", "content": build_system_prompt()}]

    def chat(self, user_message: str) -> str:
        """Process a single user message and return the final response."""
        self.messages.append({"role": "user", "content": user_message})
        
      
        final_response = self._run_loop()
        
        save_session(self.session_id, self.messages)
        
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
                max_tokens=1000
            )
            
            msg = response.choices[0].message
            
            # FIX: Convert the object to a dictionary before appending!
            # exclude_none=True ensures we don't pass null values back to the API
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
            "list_files": list_files
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
        # Changed slightly to handle the initial state clearly
        print(f"Research Desk [Session: {self.session_id}] — Type '/quit' to exit")
        print("-" * 50)
        
        while True:
            try:
                user_input = input("\n> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nExiting...")
                break
                
            if not user_input or user_input in ("/quit", "/exit"):
                print("Goodbye!")
                break
                

            response = self.chat(user_input)
            print(f"\nAgent: {response}\n")

    def _emit(self, event: str, **data) -> None:
        if event == "tool_call":
            print(f"  [Executing Tool] -> {data.get('name')}...", file=sys.stderr)


def build_system_prompt() -> str:
    """Combine base instructions with dynamic context from AGENTS.md."""
    base_prompt = "You are Research Desk, a highly capable coding assistant. You have full access to the local file system."
    agents_content = ""
    
    if os.path.exists("AGENTS.md"):
        with open("AGENTS.md", "r", encoding="utf-8") as f:
            agents_content = f.read()
            
    return f"{base_prompt}\n\n{agents_content}".strip()


def main():
    agent = REPLAgent()
    
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
        print(f"\nRunning one-shot command: '{prompt}'")
        print(agent.run_once(prompt))
    else:
        agent.run()

if __name__ == "__main__":
    main()
