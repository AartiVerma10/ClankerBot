import sys
import os
import json
from datetime import datetime
from textual.app import App, ComposeResult
from textual.screen import ModalScreen
from textual.containers import Horizontal, Vertical, Container
from textual.widgets import Header, Footer, Input, RichLog, Static
from textual import work

from agent import Agent, load_session, delete_session, create_session, build_system_prompt, SESSIONS_DIR

class NotificationModal(ModalScreen):
    """A pop-up screen to view background task notifications."""
    CSS = """
    NotificationModal { align: center middle; background: $background 50%; }
    #notif_container { width: 80%; height: 60%; border: heavy $accent; background: $surface; }
    #notif_log { padding: 1 2; }
    """
    def compose(self) -> ComposeResult:
        with Container(id="notif_container"):
            yield RichLog(id="notif_log", highlight=True, markup=True)
        yield Footer()

    def on_mount(self) -> None:
        log_widget = self.query_one(RichLog)
        notif_path = ".agent/notifications.log"
        log_widget.write("[bold cyan]=== BACKGROUND NOTIFICATIONS ===[/bold cyan]\n")
        if os.path.exists(notif_path):
            with open(notif_path, "r", encoding="utf-8") as f:
                for line in f.readlines()[-15:]:
                    log_widget.write(line.strip())
        else:
            log_widget.write("[yellow]No background jobs have completed yet.[/yellow]")
        log_widget.write("\n[dim]Press Escape to close.[/dim]")

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.app.pop_screen()


class TUIAgent(App, Agent):
    """3-Panel Dynamic Workspace for Code Scout Engine operations."""
    CSS = """
    Screen { background: #1a1a1a; }
    Horizontal { height: 1fr; }
    
    #chat-container { width: 1fr; border-right: solid #333333; padding: 1; }
    #shortcuts-container { width: 24; border-right: solid #333333; padding: 1; background: #1a1a1a; display: block; }
    #shortcuts-container.-hidden { display: none; }
    #tool-container { width: 25%; padding: 1; background: #141414; }
    
    #chat-log, #tool-log { height: 1fr; background: transparent; }
    #thinking-indicator { height: 1; color: #ffaa00; text-style: italic bold; padding-left: 1; }
    
    Input { dock: bottom; margin-top: 1; border: tall #444444; background: #222222; }
    .panel-title { text-style: bold; color: #00aaff; }
    .shortcut-text { margin-top: 1; color: #aaaaaa; }
    #persistent-hint { dock: bottom; height: 1; content-align: center middle; color: #00aaff; background: #222222; text-style: bold; }
    """
    
    BINDINGS = [
        ("ctrl+c", "quit", "Quit"),
        ("ctrl+q", "quit", "Quit"),
        ("ctrl+n", "show_notifications", "Notifs"),
        ("ctrl+h", "toggle_shortcuts", "Menu Toggle"),
        ("ctrl+x", "clear_chat", "Reset Memory"),
        ("ctrl+s", "save1", "Save Active"),
        ("ctrl+a", "save2", "Save History"),
        ("ctrl+r", "retrieve_notes", "Inject Notes")
    ]
    
    def __init__(self, session_id=None, *args, **kwargs):
        App.__init__(self, *args, **kwargs)
        Agent.__init__(self, session_id=session_id)
        # Wire presentation layer telemetry mapping to intercept tool states
        self.presentation_hook = self._emit_ui

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal():
            # Left Panel
            with Vertical(id="chat-container"):
                yield Static("CONVERSATION LOG", classes="panel-title")
                yield RichLog(id="chat-log", markup=True, wrap=False)
                yield Static("", id="thinking-indicator")
                yield Input(placeholder="Ask agent, /save1, /save2, /delete <id>, or /repl...")
            
            # Center Panel
            with Vertical(id="shortcuts-container"):
                yield Static("SHORTCUTS", classes="panel-title")
                info = (
                    "\n[bold #00ffaa]Ctrl+C[/] - Quit"
                    "\n\n[bold #00ffaa]Ctrl+N[/] - Notifs"
                    "\n\n[bold #00ffaa]Ctrl+H[/] - Toggle Menu"
                    "\n\n[bold #00ffaa]Ctrl+X[/] - Clear Memory"
                    "\n\n[bold #00ffaa]Ctrl+S[/] - Save Active"
                    "\n\n[bold #00ffaa]Ctrl+A[/] - Save History"
                    "\n\n[bold #00ffaa]Ctrl+R[/] - Inject Notes"
                )
                yield Static(info, markup=True, classes="shortcut-text")
                
            # Right Panel
            with Vertical(id="tool-container"):
                yield Static("TOOL TRACE ENGINE", classes="panel-title")
                yield RichLog(id="tool-log", markup=True, wrap=False)
                
        yield Static("💡 Press 'Ctrl+H' anywhere to toggle the shortcuts dashboard side panel bar", id="persistent-hint")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "Code Scout Workspace TUI"
        self.set_interval(1, self.update_clock)
        session_text = f"Active ID: {getattr(self, 'session_id', 'New')}"
        self.query_one("#chat-log", RichLog).write(f"[bold green]System Booted Up — {session_text}[/bold green]")

    def update_clock(self) -> None:
        self.sub_title = datetime.now().strftime("%A, %B %d, %Y")

    def _emit_ui(self, event: str, **data) -> None:
        """Presentation hook processing background operational telemetry into UI panels."""
        if event == "tool_call":
            self.call_from_thread(
                self.query_one("#tool-log", RichLog).write, 
                f"⚙️ [cyan]Executing:[/cyan] {data.get('name')}..."
            )
        elif event == "tool_result":
            trimmed = str(data.get('result'))[:75] + "..."
            self.call_from_thread(
                self.query_one("#tool-log", RichLog).write, 
                f"✅ [green]Result:[/green] {trimmed}"
            )

    def on_input_submitted(self, event: Input.Submitted) -> None:
        msg = event.value.strip()
        if not msg:
            return
        
        self.query_one(Input).value = ""
        
        # Intercept /repl command to seamlessly drop back into terminal
        if msg == "/repl":
            self.query_one("#chat-log", RichLog).write("[yellow]Switching to REPL mode...[/yellow]")
            self.exit(result="SWITCH_TO_REPL")
            return

        # Intercept save slash commands to emulate REPL behaviors
        if msg == "/save1":
            self.action_save1()
            return

        if msg == "/save2":
            self.action_save2()
            return
        
        # Intercept and process targeted removal commands directly inside the TUI context
        if msg.startswith("/delete"):
            parts = msg.split(maxsplit=1)
            if len(parts) < 2:
                self.query_one("#chat-log", RichLog).write("[bold red]Specify session ID to erase.[/bold red]")
                return
            target = parts[1].strip()
            if delete_session(target):
                self.query_one("#chat-log", RichLog).write(f"[bold red]Deleted session log: {target}[/bold red]")
                if self.session_id == target:
                    self.session_id = create_session()
                    self.messages = [{"role": "system", "content": build_system_prompt()}]
                    self.title = "Untitled"
                    self.query_one("#chat-log", RichLog).write("[yellow]Active context purged. Resetting buffer...[/yellow]")
            else:
                self.query_one("#chat-log", RichLog).write(f"[bold red]Session key '{target}' not found.[/bold red]")
            return

        self.query_one("#chat-log", RichLog).write(f"\n[bold cyan]You:[/bold cyan] {msg}")
        self.query_one("#thinking-indicator").update("[blink]ai engine running...[/blink]")
        self.run_agent_task(msg)

    @work(thread=True)
    def run_agent_task(self, msg: str) -> None:
        try:
            response = self.chat(msg)
            self.call_from_thread(self.query_one("#thinking-indicator").update, "")
            self.call_from_thread(
                self.query_one("#chat-log", RichLog).write, 
                f"[bold yellow]Agent:[/bold yellow] {response}\n"
            )
        except Exception as e:
            self.call_from_thread(self.query_one("#thinking-indicator").update, "")
            self.call_from_thread(
                self.query_one("#chat-log", RichLog).write, 
                f"[bold red]Runtime Error:[/bold red] {str(e)}"
            )

    def action_show_notifications(self) -> None:
        self.push_screen(NotificationModal())

    def action_toggle_shortcuts(self) -> None:
        panel = self.query_one("#shortcuts-container")
        panel.toggle_class("-hidden")

    def action_clear_chat(self) -> None:
        self.query_one("#chat-log", RichLog).clear()
        if self.messages:
            self.messages = [self.messages[0]]
        self.query_one("#chat-log", RichLog).write("[italic gray]--- Context History Re-Aligned ---[/italic gray]")

    def action_save1(self) -> None:
        """Fires via Ctrl+S shortcut or /save1 submission - Exports live RAM context."""
        self._export_markdown_logic(is_disk=False)

    def action_save2(self) -> None:
        """Fires via Ctrl+A shortcut or /save2 submission - Exports JSON history from disk."""
        self._export_markdown_logic(is_disk=True)

    def _export_markdown_logic(self, is_disk: bool) -> None:
        """Unified Markdown builder cleanly handling conversations and resource mapping details."""
        mode_label = "COMPLETE history from disk" if is_disk else "CURRENT active memory"
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
                f.write(f"# {header}: {getattr(self, 'session_title', 'Untitled')} ({self.session_id})\n\n")
                
                for m in target_messages:
                    role = m.get('role', 'unknown').lower()
                    content = m.get('content', '')
                    
                    # 1. Skip system prompts and raw tool data dumps completely
                    if role in ('system', 'tool'):
                        continue
                        
                    # 2. Write the User or Assistant chat text
                    if content and role in ('user', 'assistant'):
                        f.write(f"### {role.upper()}\n{content}\n\n")
                    
                    # 3. Dynamic trace gathering to present clean context summaries
                    if role == 'assistant' and m.get('tool_calls'):
                        sources = []
                        for tc in m.get('tool_calls'):
                            func = tc.get('function', {})
                            name = func.get('name', 'unknown')
                            args_str = func.get('arguments', '{}')
                            try:
                                args = json.loads(args_str)
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

            self.notify(f"Saved clean log to {path}", title="Export Complete", severity="information")
            self.query_one("#tool-log", RichLog).write(f"[green]Successfully exported {mode_label} to {path}[/green]")
        except Exception as e:
            self.notify(f"Failed writing markdown profile: {str(e)}", title="Export Failure", severity="error")

    def action_retrieve_notes(self) -> None:
        if not os.path.exists("notes"):
            self.query_one("#tool-log", RichLog).write("[yellow]No local notes directory found.[/yellow]")
            return
            
        files = [f for f in os.listdir("notes") if f.endswith(".md")]
        if not files:
            self.query_one("#tool-log", RichLog).write("[yellow]No note indexes found to compile.[/yellow]")
            return

        compiled = []
        for file in files:
            try:
                with open(os.path.join("notes", file), "r", encoding="utf-8") as f:
                    compiled.append(f"Content from {file}:\n{f.read()}")
            except Exception:
                pass

        if compiled:
            self.messages.append({
                "role": "system",
                "content": f"BACKGROUND KNOWLEDGE MANIFEST:\n{chr(10).join(compiled)}"
            })
            self.query_one("#chat-log", RichLog).write("[bold magenta]--- Synced notes payload into memory! ---[/bold magenta]")


if __name__ == "__main__":
    TUIAgent().run()