import sys
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer, Input, RichLog, Static
from textual import work


from agent import Agent

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

    def __init__(self, *args, **kwargs):
      
        App.__init__(self, *args, **kwargs)

        Agent.__init__(self)

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

if __name__ == "__main__":
    TUIAgent().run()