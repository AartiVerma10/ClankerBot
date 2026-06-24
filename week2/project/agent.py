import os
import sys
import json
import requests
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer, Input, RichLog, Static
from textual import work

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv(override=True)

# --- TOOLS ---

def web_search(query: str) -> str:
    url = "https://google.serper.dev/search"
    payload = json.dumps({"q": query})
    headers = {'X-API-KEY': os.environ.get("SERPER_API_KEY"), 'Content-Type': 'application/json'}
    response = requests.request("POST", url, headers=headers, data=payload)
    return json.dumps(response.json().get("organic", [])[:5])

def web_fetch(url: str) -> str:
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        return requests.get(url, headers=headers, timeout=10).text[:1500]
    except Exception as e: 
        return f"Error: {str(e)}"

def save_research_note(title: str, content: str) -> str:
    try:
        os.makedirs("notes", exist_ok=True)
        safe = "".join([c for c in title if c.isalnum() or c in " -_"]).lower().replace(" ", "_")
        path = os.path.join("notes", f"{safe or 'note'}.md")
        with open(path, "w", encoding="utf-8") as f: 
            f.write(f"# {title}\n\n{content}")
        return json.dumps({"status": "success", "file": path})
    except Exception as e: 
        return json.dumps({"status": "error", "message": str(e)})

# --- TUI APP ---

class AgentTUI(App):
    CSS = """
    Screen { background: #1a1a1a; }
    Horizontal { height: 1fr; }
    
    #chat-container { width: 1fr; border-right: solid #333333; padding: 1; }
    #shortcuts-container { width: 22; border-right: solid #333333; padding: 1; background: #1a1a1a; display: block; }
    #shortcuts-container.-hidden { display: none; }
    #tool-container { width: 25%; padding: 1; background: #141414; }
    
    #chat-log, #tool-log { height: 1fr; background: transparent; }
    
    /* FIXED: Blinking AI Thinking Indicator */
    #thinking-indicator { height: 1; color: #ffaa00; text-style: italic bold; padding-left: 1; }
    
    Input { dock: bottom; margin-top: 1; border: tall #444444; background: #222222; }
    .panel-title { text-style: bold; color: #00aaff; }
    .shortcut-text { margin-top: 1; color: #aaaaaa; }
    
    /* Persistent Bottom Hint */
    #persistent-hint { dock: bottom; height: 1; content-align: center middle; color: #00aaff; background: #222222; text-style: bold; }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("c", "clear_chat", "Clear Chat"),
        ("s", "save_notes", "Save Notes"),
        ("r", "retrieve_notes", "Retrieve Notes"),
        ("h", "toggle_shortcuts", "Toggle Menu") 
    ]

    def compose(self) -> ComposeResult:
        # Top right clock enabled
        yield Header(show_clock=True)
        
        with Horizontal():
            # Left Panel: Chat
            with Vertical(id="chat-container"):
                yield Static("CONVERSATION LOG", classes="panel-title")
                yield RichLog(id="chat-log", markup=True, wrap=False)
                
                #   Start empty so it reserves space without breaking layout
                yield Static("", id="thinking-indicator")
                yield Input(placeholder="Ask your agent...")
                
            # Middle Panel: Shortcuts
            with Vertical(id="shortcuts-container"):
                yield Static("SHORTCUTS", classes="panel-title")
                shortcuts_info = (
                    "\n[bold #00ffaa]Q[/] - Quit"
                    "\n\n[bold #00ffaa]C[/] - Clear Chat"
                    "\n\n[bold #00ffaa]S[/] - Save Notes"
                    "\n\n[bold #00ffaa]R[/] - Get Notes"
                    "\n\n[bold #00ffaa]H[/] - Hide Menu"
                )
                yield Static(shortcuts_info, markup=True, classes="shortcut-text")
                
            # Right Panel: Tools
            with Vertical(id="tool-container"):
                yield Static("TOOL TRACE", classes="panel-title")
                yield RichLog(id="tool-log", markup=True, wrap=False)
                
        # Bottom text hint and default footer
        yield Static("💡 Press 'H' anywhere to toggle the shortcuts panel on or off", id="persistent-hint")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "Perplexity Agent TUI"
        self.set_interval(1, self.update_clock)
        
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1", 
            api_key=os.environ.get("OPENROUTER_API_KEY")
        )
        self.history = [{
            "role": "system", 
            "content": "you are a sarcastic but extremely helpful assistant. you will never hallucinate a answer and will alawys try to use a tool whreever necesaary also use one emoji .be conscise."
        }]
        self.tools_schema = [
            {"type": "function", "function": {"name": "web_search", "description": "Search web.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
            {"type": "function", "function": {"name": "web_fetch", "description": "Fetch URL.", "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}}},
            {"type": "function", "function": {"name": "save_research_note", "description": "Save to markdown.", "parameters": {"type": "object", "properties": {"title": {"type": "string"}, "content": {"type": "string"}}, "required": ["title", "content"]}}}
        ]

    def update_clock(self) -> None:
        """Updates the header's subtitle with the current date."""
        self.sub_title = datetime.now().strftime("%A, %B %d, %Y")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        msg = event.value.strip()
        if not msg:
            return
        self.query_one(Input).value = ""
        self.query_one("#chat-log", RichLog).write(f"[bold cyan]you:[/bold cyan] {msg}")
        self.history.append({"role": "user", "content": msg})
        
        # FIXED: Inject the thinking text dynamically
        self.query_one("#thinking-indicator").update("[blink]ai is thinking...[/blink]")
        
        self.run_agent_loop()

    @work(thread=True)
    def run_agent_loop(self) -> None:
        try:
            resp = self.client.chat.completions.create(
                model="deepseek/deepseek-v4-flash", 
                messages=self.history, 
                tools=self.tools_schema, 
                max_tokens=1000
            )
            msg = resp.choices[0].message
            self.history.append(msg.model_dump(exclude_none=True))

            if msg.content:
                # FIXED: Clear thinking text when final response arrives
                self.app.call_from_thread(self.query_one("#thinking-indicator").update, "")
                self.app.call_from_thread(self.query_one("#chat-log", RichLog).write, f"[bold green]ai:[/bold green] {msg.content}")

            if msg.tool_calls:
                # FIXED: Keep thinking text on if using tools
                self.app.call_from_thread(self.query_one("#thinking-indicator").update, "[blink]ai is thinking...[/blink]")
                
                for tc in msg.tool_calls:
                    name = tc.function.name
                    args = json.loads(tc.function.arguments)
                    
                    # THIS WRITES TO YOUR TOOL PANEL:
                    self.app.call_from_thread(self.query_one("#tool-log", RichLog).write, f"executing: {name}")
                    
                    try:
                        if name == "web_search": res = web_search(args["query"])
                        elif name == "web_fetch": res = web_fetch(args["url"])
                        elif name == "save_research_note": res = save_research_note(args["title"], args["content"])
                        else: res = "error: unknown tool"
                    except Exception as e: 
                        res = str(e)
                    
                    # THIS WRITES THE RESULT TO YOUR TOOL PANEL:
                    self.app.call_from_thread(self.query_one("#tool-log", RichLog).write, f"result: {res[:80]}...")
                    self.history.append({"role": "tool", "tool_call_id": tc.id, "name": name, "content": res})
                
                self.run_agent_loop()
                    
        except Exception as e:
            # FIXED: Clear thinking text if error occurs
            self.app.call_from_thread(self.query_one("#thinking-indicator").update, "")
            self.app.call_from_thread(self.query_one("#chat-log", RichLog).write, f"[red]error: {str(e)}[/red]")

    def action_toggle_shortcuts(self) -> None:
        """Hides or shows the middle shortcuts panel on 'H'."""
        panel = self.query_one("#shortcuts-container")
        if panel.has_class("-hidden"):
            panel.remove_class("-hidden")
        else:
            panel.add_class("-hidden")

    def action_quit(self) -> None:
        self.exit()

    def action_clear_chat(self) -> None:
        self.query_one("#chat-log", RichLog).clear()
        if len(self.history) > 0:
            self.history = [self.history[0]]
        self.query_one("#chat-log", RichLog).write("[italic gray]--- Chat Memory Reset ---[/italic gray]")

    def action_save_notes(self) -> None:
        if len(self.history) <= 1:
            self.query_one("#tool-log", RichLog).write("[yellow]warn: no active logs to export[/yellow]")
            return

        md_lines = ["*Exported Session Log via Shortcut Key*:\n"]
        for msg in self.history:
            role = msg.get("role")
            if role == "user": md_lines.append(f"**User**: {msg.get('content')}\n")
            elif role == "assistant" and msg.get("content"): md_lines.append(f"**Agent**: {msg.get('content')}\n")
            elif role == "tool": md_lines.append(f" *[Executed Action: {msg.get('name')}]*\n")

        markdown_body = "\n".join(md_lines)
        response_raw = save_research_note("Manual_Session_Backup", markdown_body)
        status_data = json.loads(response_raw)

        if status_data.get("status") == "success":
            self.query_one("#tool-log", RichLog).write(f"[green]success: exported to {status_data['file']}[/green]")
        else:
            self.query_one("#tool-log", RichLog).write(f"[red]error writing note: {status_data.get('message')}[/red]")

    def action_retrieve_notes(self) -> None:
        if not os.path.exists("notes"):
            self.query_one("#tool-log", RichLog).write("[yellow]warn: 'notes' folder not found[/yellow]")
            return

        files = [f for f in os.listdir("notes") if f.endswith(".md")]
        if not files:
            self.query_one("#tool-log", RichLog).write("[yellow]warn: no saved notes found[/yellow]")
            return

        compiled_notes = []
        for file in files:
            try:
                with open(os.path.join("notes", file), "r", encoding="utf-8") as f:
                    compiled_notes.append(f"--- File: {file} ---\n{f.read()}")
            except Exception as e:
                self.query_one("#tool-log", RichLog).write(f"[red]error reading {file}: {e}[/red]")

        if compiled_notes:
            all_notes_text = "\n\n".join(compiled_notes)
            self.history.append({
                "role": "system",
                "content": f"USER'S PREVIOUSLY SAVED RESEARCH NOTES:\n{all_notes_text}\n\nUse this context if the user asks about past research."
            })
            self.query_one("#chat-log", RichLog).write(f"[bold magenta]--- Injected {len(files)} saved note(s) into memory! ---[/bold magenta]")
            self.query_one("#tool-log", RichLog).write(f"[green]retrieved {len(files)} note files[/green]")

if __name__ == "__main__":
    AgentTUI().run()
