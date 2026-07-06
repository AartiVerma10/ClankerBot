import os
import sys
import json
import asyncio
from openai import OpenAI
from dotenv import load_dotenv
from contextlib import AsyncExitStack

# Existing tools
from tools.files import read_file, write_file, edit_file, list_files
from tools.exec import run_command, check_background_job
from tools.plan import add_todos, get_todos, mark_todo, set_active_session 
from tools.search import grep, list_definitions, get_repo_map
from tools.web import web_search, web_fetch
from tools.schema import TOOLS
from tools.safety import log_notification 

# Custom component imports
from spinner import REPLSpinner
from agent_helper.sessions import (
    SESSIONS_DIR, create_session, save_session, load_session, 
    delete_session, build_system_prompt
)
from agent_helper.exploration import delegate_exploration

# Week 5: Import the MCP Manager
try:
    from tools.mcp_bridge import MCPManager
except ImportError:
    MCPManager = None

load_dotenv()

WORKSPACE_ROOT = os.path.abspath(os.environ.get("WORKSPACE_ROOT", "."))
MAIN_MAX_ITERATIONS = 20
MODEL = "deepseek/deepseek-chat"

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY"),
)

def load_config():
    if os.path.exists("config.json"):
        try:
            with open("config.json", "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            pass 
    return {"mcp_servers": {}, "active_skills": []}

def load_skill_content(skill_name: str) -> str:
    skill_path = os.path.join("skills", skill_name, "SKILL.md")
    if os.path.exists(skill_path):
        with open(skill_path, "r", encoding="utf-8") as f:
            return f.read()
    return f"Skill '{skill_name}' not found."

class Agent:
    def __init__(self, session_id=None):
        self.config = load_config()
        self.session_title = "Untitled"
        self.presentation_hook = None
        self.mcp = None 
        
        if session_id:
            self.session_id = session_id
            session_data = load_session(session_id)
            self.session_title = session_data.get("title", "Untitled") 
            self.messages = session_data.get("messages", [])
            if self.messages and self.messages[0].get("role") == "system":
                self.messages[0]["content"] = build_system_prompt()
        else:
            self.session_id = create_session()
            self.messages = [{"role": "system", "content": build_system_prompt()}]
        set_active_session(self.session_id, self.session_title)

    async def chat(self, user_message: str) -> str:
        self.messages.append({"role": "user", "content": user_message})
        final_response = await self._run_loop()
        save_session(self.session_id, self.messages, self.session_title)
        
        # Log notification for TUI/Background awareness
        short_response = final_response[:100] + "..." if len(final_response) > 100 else final_response
        log_notification(f"Task Completed: {short_response}", session_id=self.session_id)
        return final_response

    async def _run_loop(self) -> str:
        for _ in range(MAIN_MAX_ITERATIONS):
            response = client.chat.completions.create(model=MODEL, messages=self.messages, tools=TOOLS, max_tokens=1500)
            msg = response.choices[0].message
            self.messages.append(msg.model_dump())
            if not msg.tool_calls: return msg.content or ""
            
            for tool_call in msg.tool_calls:
                result_json = await self.dispatch(tool_call)
                self.messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result_json})
        return "Max iterations reached."

    async def dispatch(self, tool_call) -> str:
        name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)
        
        # Week 5 Skills Engine
        if name == "load_skill":
            return json.dumps({"status": "Skill loaded", "content": load_skill_content(args.get("skill_name"))})
        
        tool_map = {
            "read_file": read_file, "write_file": write_file, "edit_file": edit_file,
            "list_files": list_files, "web_fetch": web_fetch, "web_search": web_search,
            "run_command": run_command, "check_background_job": check_background_job,
            "add_todos": add_todos, "get_todos": get_todos, "mark_todo": mark_todo,
            "grep": grep, "list_definitions": list_definitions, "get_repo_map": get_repo_map,
            "delegate_exploration": delegate_exploration, "delete_session": delete_session
        }
        
        if name in tool_map:
            try: return json.dumps(tool_map[name](**args))
            except Exception as e: return json.dumps({"error": str(e)})
        
        # Week 5 MCP Bridge Integration
        if self.mcp:
            try: 
                print(f"[DEBUG] Attempting to call MCP tool: {name} with args {args}")
                result = await self.mcp.call_tool(name, args)
                return json.dumps(result)
            except Exception as e: 
                print(f"[DEBUG] MCP call failed: {str(e)}")
                return json.dumps({"error": str(e)})
        return json.dumps({"error": f"Tool '{name}' not found."})

class REPLAgent(Agent):
    def __init__(self, session_id=None):
        super().__init__(session_id)
        self.spinner = REPLSpinner()
        self.exit_stack = None

    async def run(self) -> None:
        print(f"\nCode Scout [Session: {self.session_id}]")
        print("Commands: /sessions, /resume, /delete, /save1, /save2, /tui")

        if MCPManager:
            self.exit_stack = AsyncExitStack()
            self.mcp = MCPManager(self.config, self.exit_stack)
            await self.mcp.connect_all()
            TOOLS.extend(await self.mcp.get_all_tools())

        while True:
            try:
                # In an async loop, standard input() is blocking, but acceptable for a simple REPL.
                user_input = input("\n> ").strip()
                if not user_input:
                    continue
                if user_input in ("/quit", "/exit"):
                    break

                # --- BACKGROUND NOTIFICATIONS ---
                if user_input in ("/notifs", "/notifications"):
                    print("\n\033[96m=== BACKGROUND NOTIFICATIONS ===\033[0m")
                    notif_path = ".agent/notifications.log"
                    if os.path.exists(notif_path):
                        with open(notif_path, "r") as f:
                            for line in f.readlines()[-5:]:
                                print(line.strip())
                    else:
                        print("No background jobs have completed yet.")
                    continue

                # --- LIST SESSIONS ---
                if user_input == "/sessions":
                    print("\nPast Sessions:")
                    if os.path.exists(SESSIONS_DIR):
                        for f in os.listdir(SESSIONS_DIR):
                            if f.endswith(".json"):
                                sid = f.replace(".json", "")
                                session_data = load_session(sid)
                                print(f" - {sid} : {session_data.get('title', 'Untitled')}")
                    continue

                # --- SAVE COMMANDS (/save1, /save2) ---
                if user_input in ("/save1", "/save2"):
                    is_disk = (user_input == "/save2")
                    mode_name = "COMPLETE history from disk" if is_disk else "CURRENT active memory"
                    print(f"\n[Exporting {mode_name} for session '{self.session_id}'...]")
                    
                    try:
                        os.makedirs("notes", exist_ok=True)
                        prefix = "save2_history" if is_disk else "save1_session"
                        path = os.path.join("notes", f"{prefix}_{self.session_id}.md")
                        
                        target_messages = load_session(self.session_id).get("messages", []) if is_disk else self.messages

                        with open(path, "w", encoding="utf-8") as f:
                            header = "Complete History Export" if is_disk else "Current Session Export"
                            f.write(f"# {header}: {self.session_title} ({self.session_id})\n\n")
                            
                            for m in target_messages:
                                role = m.get('role', 'unknown').lower()
                                content = m.get('content', '')
                                
                                if role in ('system', 'tool'):
                                    continue
                                    
                                if content and role in ('user', 'assistant'):
                                    f.write(f"### {role.upper()}\n{content}\n\n")
                                
                                if role == 'assistant' and m.get('tool_calls'):
                                    sources = []
                                    for tc in m.get('tool_calls', []):
                                        func = tc.get('function', {})
                                        name = func.get('name', 'unknown')
                                        try:
                                            args = json.loads(func.get('arguments', '{}'))
                                            if name == "web_fetch":
                                                sources.append(f"- **Fetched Link:** {args.get('url', '')}")
                                            elif name == "web_search":
                                                sources.append(f"- **Web Search:** '{args.get('query', '')}'")
                                            elif name == "read_file":
                                                sources.append(f"- **Read File:** `{args.get('file_path', '')}`")
                                        except Exception:
                                            pass
                                    if sources:
                                        f.write("**Sources & Context Gathered:**\n" + "\n".join(sources) + "\n\n")
                        print(f"\033[92m[Success: Saved clean conversation to {path}]\033[0m")
                    except Exception as e:
                        print(f"\033[91m[Export failure: {str(e)}]\033[0m")
                    continue

                # --- DELETE SESSION ---
                if user_input.startswith("/delete"):
                    parts = user_input.split(maxsplit=1)
                    if len(parts) < 2:
                        print("[Error: Specify session ID to delete. E.g., /delete abc123xyz]")
                    elif delete_session(parts[1].strip()):
                        print(f"[Successfully deleted session: {parts[1].strip()}]")
                        if self.session_id == parts[1].strip():
                            self.session_id = create_session()
                            self.messages = [{"role": "system", "content": build_system_prompt()}]
                            self.session_title = "Untitled"
                    else:
                        print(f"[Error: Session '{parts[1].strip()}' not found]")
                    continue

                # --- RESUME SESSION ---
                if user_input.startswith("/resume"):
                    parts = user_input.split(maxsplit=1)
                    if len(parts) < 2:
                        print("[Error: Provide a session ID. Example: /resume abc123xyz]")
                    else:
                        target_id = parts[1].strip()
                        file_path = os.path.join(SESSIONS_DIR, f"{target_id}.json")
                        if os.path.exists(file_path):
                            self.session_id = target_id
                            session_data = load_session(target_id)
                            self.session_title = session_data.get("title", "Untitled")
                            set_active_session(self.session_id, self.session_title) 
                            self.messages = session_data.get("messages", [])
                            print(f"\n[Successfully resumed session: {self.session_title} ({target_id})]")
                        else:
                            print(f"\n[Error: Session '{target_id}' not found]")
                    continue
                
                # --- TUI SWITCH ---
                if user_input in ("/tui", "/ui"):
                    print(f"\n[Booting up Textual UI for session '{self.session_id}'...]")
                    try:
                        from tui import TUIAgent
                        if TUIAgent(session_id=self.session_id).run() == "SWITCH_TO_REPL":
                            print(f"\n[Switched back to REPL for session '{self.session_id}']\n" + "-" * 50)
                            continue
                        break
                    except ImportError:
                        print("[Error: Could not import TUIAgent from tui.py]")
                    continue
                
                # --- CHAT INTERACTION ---
                self.spinner.update_msg("Agent is thinking...")
                self.spinner.start()
                try:
                    response = await self.chat(user_input)
                finally:
                    self.spinner.stop()
                print(f"\nAgent: {response}\n")

            except Exception as e:
                print(f"\n[Error: {e}]")

async def main():
    agent = REPLAgent()
    await agent.run()

if __name__ == "__main__":
    asyncio.run(main())