import os
import sys
import json
from openai import OpenAI
from dotenv import load_dotenv

# Tool imports
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
    SESSIONS_DIR, 
    create_session, 
    save_session, 
    load_session, 
    delete_session, 
    build_system_prompt
)
from agent_helper.exploration import delegate_exploration

load_dotenv()

WORKSPACE_ROOT = os.path.abspath(os.environ.get("WORKSPACE_ROOT", "."))
MAIN_MAX_ITERATIONS = 20
SCOUT_MAX_ITERATIONS = 8

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY"),
)

MODEL = "deepseek/deepseek-chat"


class Agent:
    def __init__(self, session_id=None):
        self.session_title = "Untitled"
        self.presentation_hook = None  # UI hook to stream tool logs
        
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

    def chat(self, user_message: str) -> str:
        self.messages.append({"role": "user", "content": user_message})
        final_response = self._run_loop()
        
        if self.session_title == "Untitled":
            try:
                title_prompt = f"Summarize this request in 5 words or less. Output ONLY the summary: '{user_message}'"
                title_response = client.chat.completions.create(
                    model=MODEL,
                    messages=[{"role": "user", "content": title_prompt}],
                    max_tokens=15
                )
                self.session_title = title_response.choices[0].message.content.strip().replace('"', '')
                set_active_session(self.session_id, self.session_title)
            except Exception:
                self.session_title = user_message[:35] + "..."
                set_active_session(self.session_id, self.session_title)

        save_session(self.session_id, self.messages, self.session_title)
        
        short_response = final_response[:150] + "..." if len(final_response) > 150 else final_response
        log_notification(
            f"Prompt Completed: '{self.session_title}' - Final Remarks: {short_response}", 
            session_id=self.session_id,
            session_title=self.session_title
        )
        
        return final_response

    def run_once(self, prompt: str) -> str:
        return self.chat(prompt)

    def _run_loop(self) -> str:
        for _ in range(MAIN_MAX_ITERATIONS):
            response = client.chat.completions.create(
                model=MODEL,
                messages=self.messages,
                tools=TOOLS,
                max_tokens=1500
            )
            
            msg = response.choices[0].message
            self.messages.append(msg.model_dump())

            if not msg.tool_calls:
                try:
                    todo_data = get_todos()
                    todos = todo_data.get("todos", [])
                    active_tasks = [t for t in todos if t.get("status") in ("pending", "in_progress", "error")]
                    
                    if active_tasks:
                        nudge = (
                            "System: Your todo list still has pending, in_progress, or error items. "
                            "You must continue working through your plan, verify your changes with commands, "
                            "and update the list statuses."
                        )
                        self.messages.append({"role": "user", "content": nudge})
                        save_session(self.session_id, self.messages, self.session_title)
                        continue
                except Exception:
                    pass 
                
                return msg.content or ""
            
            for tool_call in msg.tool_calls:
                if self.presentation_hook:
                    self.presentation_hook("tool_call", name=tool_call.function.name)
                
                result_json = self.dispatch(tool_call)
                
                if self.presentation_hook:
                    self.presentation_hook("tool_result", name=tool_call.function.name, result=result_json)
                    
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result_json
                })
                save_session(self.session_id, self.messages, self.session_title)
                
        return "Error: Maximum iterations reached without resolving the task or completing the plan."

    def dispatch(self, tool_call) -> str:
        name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)
        
        tool_map = {
            "read_file": read_file,
            "write_file": write_file,
            "edit_file": edit_file,
            "list_files": list_files,
            "web_fetch": web_fetch,
            "web_search": web_search,
            "run_command": run_command,
            "check_background_job": check_background_job,
            "add_todos": add_todos,
            "get_todos": get_todos,
            "mark_todo": mark_todo,
            "grep": grep,
            "list_definitions": list_definitions,
            "get_repo_map": get_repo_map,
            "delegate_exploration": delegate_exploration,
            "delete_session": delete_session
        }
        
        if name in tool_map:
            try:
                result_dict = tool_map[name](**args)
                return json.dumps(result_dict)
            except Exception as e:
                return json.dumps({"error": f"Tool execution failed: {str(e)}"})
                
        return json.dumps({"error": f"Tool '{name}' is not recognized."})


class REPLAgent(Agent):
    def __init__(self, session_id=None):
        super().__init__(session_id)
        self.spinner = REPLSpinner()
        self.presentation_hook = self._emit_cli

    def _emit_cli(self, event: str, **data) -> None:
        if event == "tool_call":
            self.spinner.update_msg(f"Executing: {data.get('name')}...")
        elif event == "tool_result":
            self.spinner.update_msg("Agent is thinking...")

    def run(self) -> None:
        print("-" * 50)
        print(f"\nCode Scout [Session: {self.session_id}] — Type '/quit' to exit")
        print("\nCommands: '/sessions', '/resume <id>', '/delete <id>', '/save1', '/save2', or '/tui' for visual mode.")
        print("-" * 50)
        
        while True:
            try:
                user_input = input("\n> ").strip()
            except (EOFError, KeyboardInterrupt):
                break
                
            if not user_input or user_input in ("/quit", "/exit"):
                print("Goodbye!")
                break
                
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

            if user_input == "/sessions":
                print("\nPast Sessions:")
                if os.path.exists(SESSIONS_DIR):
                    for f in os.listdir(SESSIONS_DIR):
                        if f.endswith(".json"):
                            sid = f.replace(".json", "")
                            session_data = load_session(sid)
                            print(f" - {sid} : {session_data.get('title', 'Untitled')}")
                continue
            
            # --- NEW SAVE COMMANDS (FILTERED FOR READABILITY) ---
            if user_input in ("/save1", "/save2"):
                is_disk = (user_input == "/save2")
                mode_name = "COMPLETE history from disk" if is_disk else "CURRENT active memory"
                print(f"\n[Exporting {mode_name} for session '{self.session_id}'...]")
                
                try:
                    os.makedirs("notes", exist_ok=True)
                    prefix = "save2_history" if is_disk else "save1_session"
                    path = os.path.join("notes", f"{prefix}_{self.session_id}.md")
                    
                    target_messages = self.messages
                    if is_disk:
                        disk_data = load_session(self.session_id)
                        target_messages = disk_data.get("messages", [])

                    with open(path, "w", encoding="utf-8") as f:
                        header = "Complete History Export" if is_disk else "Current Session Export"
                        f.write(f"# {header}: {self.session_title} ({self.session_id})\n\n")
                        
                        for m in target_messages:
                            role = m.get('role', 'unknown').lower()
                            content = m.get('content', '')
                            
                            # 1. Skip system prompts and raw tool data dumps entirely
                            if role in ('system', 'tool'):
                                continue
                                
                            # 2. Write the User or Assistant chat content
                            if content and role in ('user', 'assistant'):
                                f.write(f"### {role.upper()}\n{content}\n\n")
                            
                            # 3. Extract tool calls to create a clean "Sources Used" summary
                            if role == 'assistant' and m.get('tool_calls'):
                                sources = []
                                for tc in m.get('tool_calls'):
                                    func = tc.get('function', {})
                                    name = func.get('name', 'unknown')
                                    args_str = func.get('arguments', '{}')
                                    try:
                                        args = json.loads(args_str)
                                        # Only extract the relevant links and queries
                                        if name == "web_fetch":
                                            sources.append(f"- **Fetched Link:** {args.get('url', '')}")
                                        elif name == "web_search":
                                            sources.append(f"- **Web Search:** '{args.get('query', '')}'")
                                        elif name == "read_file":
                                            sources.append(f"- **Read File:** `{args.get('file_path', '')}`")
                                    except Exception:
                                        pass
                                
                                if sources:
                                    f.write("**Sources & Context Gathered:**\n")
                                    f.write("\n".join(sources) + "\n\n")

                    print(f"\033[92m[Success: Saved clean conversation to {path}]\033[0m")
                except Exception as e:
                    print(f"\033[91m[Export failure: {str(e)}]\033[0m")
                continue
            # ----------------------------------------------------

            if user_input.startswith("/delete"):
                parts = user_input.split(maxsplit=1)
                if len(parts) < 2:
                    print("[Error: Specify session ID to delete. E.g., /delete abc123xyz]")
                    continue
                target_id = parts[1].strip()
                if delete_session(target_id):
                    print(f"[Successfully deleted session: {target_id}]")
                    if self.session_id == target_id:
                        print("[Wiped current active session. Spawning new environment...]")
                        self.session_id = create_session()
                        self.messages = [{"role": "system", "content": build_system_prompt()}]
                        self.session_title = "Untitled"
                else:
                    print(f"[Error: Session '{target_id}' not found]")
                continue

            if user_input.startswith("/resume"):
                parts = user_input.split(maxsplit=1)
                if len(parts) < 2:
                    print("[Error: Provide a session ID. Example: /resume abc123xyz]")
                    continue
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
                
            if user_input in ("/tui", "/ui"):
                print(f"\n[Booting up Textual UI for session '{self.session_id}'...]")
                try:
                    from tui import TUIAgent
                    app = TUIAgent(session_id=self.session_id)
                    result = app.run()
                    
                    if result == "SWITCH_TO_REPL":
                        print(f"\n[Switched back to REPL for session '{self.session_id}']")
                        print("-" * 50)
                        continue
                    
                    print("Exiting Code Scout.")
                    break
                except ImportError:
                    print("[Error: Could not import TUIAgent from tui.py]")
                continue
                
            self.spinner.update_msg("Agent is thinking...")
            self.spinner.start()
            try:
                response = self.chat(user_input)
            finally:
                self.spinner.stop()
                
            print(f"\nAgent: {response}\n")


def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == "--session" and len(sys.argv) > 3:
            session_id = sys.argv[2]
            prompt = " ".join(sys.argv[3:])
            agent = REPLAgent(session_id=session_id)
            print(agent.run_once(prompt))
        elif sys.argv[1] == "--tui":
            from tui import TUIAgent
            resume_id = sys.argv[2] if len(sys.argv) > 2 else None
            app = TUIAgent(session_id=resume_id)
            result = app.run()
            
            if result == "SWITCH_TO_REPL":
                print(f"\n[Dropping into REPL for session '{app.session_id}']")
                agent = REPLAgent(session_id=app.session_id)
                agent.run()
        else:
            prompt = " ".join(sys.argv[1:])
            agent = REPLAgent()
            print(agent.run_once(prompt))
    else:
        agent = REPLAgent()
        agent.run()

if __name__ == "__main__":
    main()