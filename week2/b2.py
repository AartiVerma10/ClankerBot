"""
Build 2: Tool Calling with the OpenAI SDK
==========================================
Build 1 had you implement the tool-call round-trip by hand using a custom text format.
This build does the same thing the production way: using the OpenAI SDK's native
`tools` parameter, `tool_calls` response field, and `"role": "tool"` messages.

The mechanics are identical. You're still parsing a tool name, running a function,
and sending the result back. The difference is that the SDK handles the encoding
and the model is trained to produce structured JSON tool calls rather than freeform XML.

Implement the same two tools as Build 1:
  - get_weather(city: str) -> dict
  - calculate(expression: str) -> dict

Then complete the agent loop and watch the pattern become clean.

Stretch goals (not required):
  - Add a third tool: get_time(timezone: str) -> dict
  - Handle multiple tool_calls in a single response (the model can call several at once)
  - Add a token counter that prints total tokens used after the loop ends
"""
import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

MODEL = "deepseek/deepseek-chat"

# ---------------------------------------------------------------------------
# Tool schemas
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Returns the current weather for a given city.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "The city name"},
                    "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Evaluates a math expression.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "e.g. '1337 * 42'"}
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_timezone",
            "description": "Tells the time, date, or day for a place.",
            "parameters": {
                "type": "object",
                "properties": {
                    "place": {"type": "string"},
                    "zone": {"type": "string", "description": "e.g. 'day', 'time', 'date'"},
                },
                "required": ["place", "zone"],
            },
        },
    },
]

# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

def get_weather(city: str, unit: str = "celsius") -> dict:
    return {"city": city, "temperature": 25, "unit": unit, "condition": "sunny"}

def calculate(expression: str) -> dict:
    try:
        # Note: eval() is dangerous in production; this is for demo only
        return {"result": eval(expression)}
    except Exception as e:
        return {"error": str(e)}

def get_timezone(place: str, zone: str) -> dict:
    return {"place": place, "zone": zone, "value": "Current data for " + place}

TOOL_REGISTRY = {
    "get_weather": get_weather,
    "calculate": calculate,
    "get_timezone": get_timezone,
}

# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

def dispatch(tool_call) -> str:
    name = tool_call.function.name
    arguments = json.loads(tool_call.function.arguments)
    
    func = TOOL_REGISTRY.get(name)
    if not func:
        return json.dumps({"error": f"Unknown tool: {name}"})
    
    result = func(**arguments)
    return json.dumps(result)

# ---------------------------------------------------------------------------
# Agent loop
# ---------------------------------------------------------------------------

MAX_ITERATIONS = 8

def run_agent(user_message: str) -> str:
    messages = [
        {"role": "system", "content": "You are a helpful assistant. Use tools when appropriate."},
        {"role": "user", "content": user_message},
    ]

    for _ in range(MAX_ITERATIONS):
        response = client.chat.completions.create(
            model=MODEL, messages=messages, tools=TOOLS, max_tokens=200,
        )
        message = response.choices[0].message
        
        if message.tool_calls:
            messages.append(message) 
            for tool_call in message.tool_calls:
                print(f"--> Executing: {tool_call.function.name}")
                result = dispatch(tool_call)
                # Append tool result
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })
        elif message.content:
            return message.content

    return "[Agent stopped after MAX_ITERATIONS]"

if __name__ == "__main__":
    test_queries = [
        "What's the weather in Tokyo?",
        "Calculate: (2**10) - 1",
        "Compare the weather in London and Delhi, and tell me what 451 * 3 is.",
    ]

    for query in test_queries:
        print(f"\n{'='*60}\nQuery: {query}\n{'='*60}")
        result = run_agent(query)
        print(f"\n\n{result}")