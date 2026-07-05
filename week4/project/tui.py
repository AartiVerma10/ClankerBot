import sys
import os
from textual.app import App, ComposeResult
from textual.screen import ModalScreen
from textual.containers import Horizontal, Vertical, Container
from textual.widgets import Header, Footer, Input, RichLog, Static
from textual import work

from agent import Agent

class NotificationModal(ModalScreen):
    """A pop-up screen to view background task notifications."""
    
    # CSS to style the modal so it floats in the center
    CSS = """
    NotificationModal {
        align: center middle;
        background: $background 50%;
    }
    #notif_container {
        width: 80%;
        height: 60%;
        border: heavy $accent;
        background: $surface;
    }
    #notif_log {
        padding: 1 2;
    }
    """

    def compose(self) -> ComposeResult:
        # A container to hold the log and give it a nice border
        with Container(id="notif_container"):
            yield RichLog(id="notif_log", highlight=True, markup=True)
        yield Footer()

    def on_mount(self) -> None:
        """Fires when the user opens the modal. Loads the latest logs."""
        log_widget = self.query_one(RichLog)
        notif_path = ".agent/notifications.log"
        
        log_widget.write("[bold cyan]=== BACKGROUND NOTIFICATIONS ===[/bold cyan]\n")
        
        if os.path.exists(notif_path):
            with open(notif_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                # Show the last 15 notifications
                for line in lines[-15:]:
                    log_widget.write(line.strip())
        else:
            log_widget.write("[yellow]No background jobs have completed yet.[/yellow]")
            
        log_widget.write("\n[dim]Press Escape to close.[/dim]")

    def on_key(self, event) -> None:
        """Close the modal when the user presses Escape."""
        if event.key == "escape":
            self.app.pop_screen()


class TUIAgent(App, Agent):
    """Textual UI version of the Agent. Uses Multiple Inheritance to act as both a UI and an Agent."""

    CSS = """
    Screen { background: #1a1a1a; }
    Horizontal { height: 1fr; }
    #chat-container { width: 80%; border-right: solid #333333; padding: 1; }
    #tool-container { width: 20%; padding: 1; background: #141414; }
    #chat-log, #tool-log { height: 1fr; background: transparent; }
    Input { dock: bottom; margin-top: 1; border: tall #444444; background: #222222; }
    .panel-title { text-style: bold; color: #00aaff; }
    """
    
    BINDINGS = [
        ("ctrl+c", "quit", "Quit App"),
        ("ctrl+q", "quit", "Quit App"),
        ("ctrl+n", "show_notifications", "Notifications (Ctrl+N)")
    ]
    
    def __init__(self, session_id=None, *args, **kwargs):
        App.__init__(self, *args, **kwargs)
        Agent.__init__(self, session_id=session_id)

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with Vertical(id="chat-container"):
                yield Static("CONVERSATION LOG", classes="panel-title")
                yield RichLog(id="chat-log", markup=True, wrap=False)
                yield Input(placeholder="Ask Research Desk...")
            with Vertical(id="tool-container"):
                yield Static("TOOL EXECUTION TRACE", classes="panel-title")
                yield RichLog(id="tool-log", markup=True, wrap=False)
        yield Footer()

    def on_mount(self) -> None:
        session_text = f"Session ID: {getattr(self, 'session_id', 'New')}"
        self.query_one("#chat-log", RichLog).write(f"[bold green]Research Desk Initialized — {session_text}[/bold green]")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        msg = event.value.strip()
        if not msg:
            return
        
        self.query_one(Input).value = ""
        self.query_one("#chat-log", RichLog).write(f"\n[bold cyan]You:[/bold cyan] {msg}")
        
        self.run_agent_task(msg)

    @work(thread=True)
    def run_agent_task(self, msg: str) -> None:
        """Runs the blocking LLM loop in a background thread so the UI doesn't freeze."""
        try:
            response = self.chat(msg)
            
            self.call_from_thread(
                self.query_one("#chat-log", RichLog).write, 
                f"[bold yellow]Agent:[/bold yellow] {response}\n"
            )
        except Exception as e:
            self.call_from_thread(
                self.query_one("#chat-log", RichLog).write, 
                f"[bold red]Error:[/bold red] {str(e)}"
            )

    def _emit(self, event: str, **data) -> None:
        """The presentation hook: Intercepts tool calls from the Agent and prints them to the side panel."""
        if event == "tool_call":
            tool_name = data.get('name')
            self.call_from_thread(
                self.query_one("#tool-log", RichLog).write, 
                f"⚙️ [cyan]Executing:[/cyan] {tool_name}..."
            )

    def action_show_notifications(self) -> None:
        """Action tied to the ctrl+n binding to open the modal."""
        self.push_screen(NotificationModal())

if __name__ == "__main__":
    TUIAgent().run()