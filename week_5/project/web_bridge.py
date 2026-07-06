from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from agent import Agent

app = FastAPI()

# Allow the browser to talk to the Python server
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"])

# Initialize your Agent
agent = Agent()

@app.post("/chat")
async def chat_with_agent(request: Request):
    data = await request.json()
    user_message = data.get("message")
    # Call your existing Agent chat logic
    response = agent.chat(user_message)
    return {"response": response}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)