"""
Build 1: Custom Tool Call Parser
=================================
Before modern SDKs handled tool calls natively, developers used custom text formats
that the model was prompted to emit. This build has you implement that pattern from
scratch: prompt the model to emit tool calls in a structured format, parse them, run
the corresponding Python function, and feed the result back.

This is NOT the production way to do it (Build 2 is). But doing it manually first
makes the mechanics obvious. The SDK is doing exactly this, just more robustly.

The format we'll use:
    The model emits tool calls wrapped in <tool_call> tags, like:

        I need to read the file first.

        <tool_call>
        {"name": "read_file", "arguments": {"path": "notes.txt"}}
        </tool_call>

    Your code finds the tag, parses the JSON, runs the function, and injects
    the result back as a <tool_response> in the next message.

Tasks:
  1. Complete `parse_tool_call` to extract name + arguments from a model response
  2. Complete `dispatch` to route a tool call to the right Python function
  3. Complete `run_agent` to implement the back-and-forth loop

Tools to implement:
  - read_file(path: str) -> dict    reads a file from disk and returns its content
  - write_file(path: str, content: str) -> dict    writes content to a file on disk

Before running, create a file called `sample.txt` with some text in it.
"""


import os
import re
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

MODEL = "deepseek/deepseek-v4-flash:free"

SYSTEM_PROMPT = """You are a helpful file assistant with access to the following tools:

- read_file(path: str): reads a file from disk and returns its content
- write_file(path: str, content: str): writes content to a file on disk

When you need to use a tool, emit EXACTLY this format and nothing else after it:

<tool_call>
{"name": "TOOL_NAME", "arguments": {"arg1": "value1"}}
</tool_call>

After you receive the tool result in a <tool_response> block, continue your response
normally. Do not emit a tool_call and prose in the same turn. Pick one or the other.
"""

# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

def read_file(path: str) -> dict:
    try:
        with open(path, "r") as fin:
            data = fin.read()
            return {"content": data, "path": path}
    except Exception as e:
        return {"error": f"Could not read the file: {str(e)}"}

def write_file(path: str, content: str) -> dict:
    try:
        with open(path, "a") as fin:
            fin.write(content)
            return {"success": True, "message": "Written successfully"}
    except Exception as e:
        return {"error": f"Could not write to file: {str(e)}"}

# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def parse_tool_call(response_text: str) -> dict | None:
    # Captures the JSON body inside <tool_call> tags
    match = re.search(r"<tool_call>(.*?)</tool_call>", response_text, flags=re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            print("Failed to parse JSON inside tags")
            return None
    return None

def strip_tool_call(response_text: str) -> str:
    return re.sub(r"<tool_call>.*?</tool_call>", "", response_text, flags=re.DOTALL).strip()

# ---------------------------------------------------------------------------
# Dispatcher (Manual routing)
# ---------------------------------------------------------------------------

def dispatch(name: str, arguments: dict) -> str:
    try:
        if name == "read_file":
            result = read_file(**arguments)
            return json.dumps(result)
        elif name == "write_file":
            result = write_file(**arguments)
            return json.dumps(result)
        else:
            return json.dumps({"error": f"Unknown tool: {name}"})
    except Exception as e:
        return json.dumps({"error": f"Dispatcher error: {str(e)}"})

# ---------------------------------------------------------------------------
# Agent loop
# ---------------------------------------------------------------------------

MAX_ITERATIONS = 6

def run_agent(user_message: str) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    for iteration in range(MAX_ITERATIONS):
        response = client.chat.completions.create(model="deepseek/deepseek-chat", max_tokens=400,messages=messages)
        content = response.choices[0].message.content
        messages.append({"role": "assistant", "content": content})

        tool_call = parse_tool_call(content)
        
        if tool_call:
            print(f"--> Executing tool: {tool_call['name']} with {tool_call['arguments']}")
            tool_result = dispatch(tool_call['name'], tool_call['arguments'])
            
            # The model sees the result as a "user" message
            messages.append({
                "role": "user", 
                "content": f"<tool_response>\n{tool_result}\n</tool_response>"
            })
        else:
            return content

    return f"[Agent stopped after {MAX_ITERATIONS} iterations]"

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    with open("sample.txt", "w") as f:
        f.write("IIT Delhi was established in 1961. It is one of the premier engineering institutions in India.\n")
        f.write("The campus spans 325 acres in Hauz Khas, New Delhi.\n")

    test_queries = [
        "Read sample.txt and summarise what it says.",
        "Read sample.txt and write a one-sentence version of its content to summary.txt.",
    ]

    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"{'='*60}")
        result = run_agent(query)
        print(f"Answer: {result}")