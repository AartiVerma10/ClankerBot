import os
import sys
import json
import requests
from openai import OpenAI
from dotenv import load_dotenv
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer, Input, RichLog, Static
from textual import work

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv(override=True)


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
    except Exception as e: return f"Error: {str(e)}"

def save_research_note(title: str, content: str) -> str:
    try:
        os.makedirs("notes", exist_ok=True)
        safe = "".join([c for c in title if c.isalnum() or c in " -_"]).lower().replace(" ", "_")
        path = os.path.join("notes", f"{safe or 'note'}.md")
        with open(path, "w", encoding="utf-8") as f: f.write(f"# {title}\n\n{content}")
        return json.dumps({"status": "success", "file": path})
    except Exception as e: return json.dumps({"status": "error", "message": str(e)})



class AgentTUI(App):
    CSS = """
    Screen { background: #1a1a1a; }
    Horizontal { height: 1fr; }
    #chat-container { width: 80%; border-right: solid #333333; padding: 1; }
    #tool-container { width: 20%; padding: 1; background: #141414; }
    #chat-log, #tool-log { height: 1fr; background: transparent; }
    Input { dock: bottom; margin-top: 1; border: tall #444444; background: #222222; }
    .panel-title { text-style: bold; color: #00aaff; }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with Vertical(id="chat-container"):
                yield Static("CONVERSATION LOG", classes="panel-title")
                yield RichLog(id="chat-log", markup=True, wrap=False)
                yield Input(placeholder="Ask your agent...")
            with Vertical(id="tool-container"):
                yield Static("TOOL EXECUTION TRACE", classes="panel-title")
                yield RichLog(id="tool-log", markup=True, wrap=False)
        yield Footer()

    def on_mount(self) -> None:
        self.client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=os.environ.get("OPENROUTER_API_KEY"))
        self.history = [{
            "role": "system", 
            "content": "you are a sarcastic but helpful assistant. order of answering: first give the answer, then be sarcastic. act like a gen alpha teen, talk in brainrot, be extremely harsh or toxic/sarcastic, talk in shakespearian english but simple, also talk in gang language like gang,chat,twin type shit. always reply in all lowercase letters and use at least one emoji. but be short."
        }]
        self.tools_schema = [
            {"type": "function", "function": {"name": "web_search", "description": "Search web.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
            {"type": "function", "function": {"name": "web_fetch", "description": "Fetch URL.", "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}}},
            {"type": "function", "function": {"name": "save_research_note", "description": "Save to markdown.", "parameters": {"type": "object", "properties": {"title": {"type": "string"}, "content": {"type": "string"}}, "required": ["title", "content"]}}}
        ]

    def on_input_submitted(self, event: Input.Submitted) -> None:
        msg = event.value.strip()
        self.query_one(Input).value = ""
        self.query_one("#chat-log", RichLog).write(f"[bold cyan]you:[/bold cyan] {msg}")
        self.history.append({"role": "user", "content": msg})
        self.run_agent_loop()

    @work(thread=True)
    def run_agent_loop(self) -> None:
        try:
            
            resp = self.client.chat.completions.create(
                model="deepseek/deepseek-chat", messages=self.history, tools=self.tools_schema, max_tokens=1000
            )
            msg = resp.choices[0].message
            
           
            if msg.content:
                self.app.call_from_thread(self.query_one("#chat-log", RichLog).write, f"ai: {msg.content}")
                self.history.append({"role": "assistant", "content": msg.content})
            
          
            if msg.tool_calls:
                for tc in msg.tool_calls:
                    name = tc.function.name
                    args = json.loads(tc.function.arguments)
                    self.app.call_from_thread(self.query_one("#tool-log", RichLog).write, f"executing: {name}")
                    
                    try:
                        if name == "web_search": res = web_search(args["query"])
                        elif name == "web_fetch": res = web_fetch(args["url"])
                        elif name == "save_research_note": res = save_research_note(args["title"], args["content"])
                        else: res = "error: unknown tool"
                    except Exception as e: res = str(e)
                    
                    self.app.call_from_thread(self.query_one("#tool-log", RichLog).write, f"result: {res[:80]}...")
                    self.history.append({"role": "tool", "tool_call_id": tc.id, "name": name, "content": res})
                    self.run_agent_loop()
                    
        except Exception as e:
            self.app.call_from_thread(self.query_one("#chat-log", RichLog).write, f"[red]error: {str(e)}[/red]")

if __name__ == "__main__":
    AgentTUI().run()