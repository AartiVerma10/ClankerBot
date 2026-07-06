#                              **-Multi Model ChatAgent-**
(Week1's work-)


This is a highly interactive, terminal based AI ChatAgent built in Python.
This project connects to the OpenRouter API, allowing users to chat with multiple Large Language Models (like DeepSeek, GPT-3.5, and Claude 3) directly from their command line.
Or if they want to interact with another LLM , they can input it as well. 

It features a custom system prompt that gives the agent a personality of Gen-Alpha with Shakespearean English while doing advanced memory management and real time streaming.



# **Work flow-**
## Initial setup: 
   - First line the program line is -
   -  `if __name__ == "__main__: setup()` which is always true and will go to function setup(). 
   - `setup()` functions consists of thefirst interface, you will see when you run the program.
   - Here The user can chose their model.
   - in `my_agent = ChatAgent(model_id=selected_model,  system_prompt=exact_system_prompt, max_turns=3)` 
   - We will fill in its model id, system prompt, maximum turns accordingly from the input.
   - lastly `my_agent.run()` will go over to the ChatAgent class's run methon.

## ChatAgent class:
   - `def run(self):`
      - It is the main method under ChatAgent class which will go in a infinity loop until instructed to be exited.
      - It has the `while True:`
      - User will here give their input and according to the input which can be to exit, reset, compact, token enquiry or to chat the flow will go to its particular code.

   - Before we dive into any particular method. Lets undersatnd our attributes and how it works.
---
   - `def __init__():`

   ```python
   class ChatAgent:
      def __init__(self, model_id, system_prompt, max_turns= 5):
        self.model_id = model_id
        self.max_turns = max_turns
        self.system_prompt = system_prompt
        self.last_usage = None # Token tracker

        self.history = [{"role": "system", "content": self.system_prompt}]
              
        api_key = os.environ.get("OPENROUTER_API_KEY")

        if not api_key:
            raise ValueError("OPENROUTER_API_KEY not found in environment variables. Please check your .env file.")
            
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key.strip(),
        )
   ```
   - its uses-
      - 1. It will connect all the inputs given in the setup fuction by equating it with the class's attributes.
      - 2. Connecting it will get the api key and connect it with the client 
      - 3. Initialise a list called history which will contain all the conversation data.
---
   - `def call_model():`   

   ```python
   def call_model(self, messages: list, stream: bool = True):
        
        api_args = {
            "model": self.model_id,
            "messages": messages,
            "stream": stream
        }
        
        
        if stream:
            api_args["stream_options"] = {"include_usage": True}

        return self.client.chat.completions.create(**api_args)
   ```
   - its uses-
      - Whenever the `def run()` function is running and receiving the input
      - Next it will append the input to the history list
      - this new history should be linked to the client of open router who will call the agent and get its response.
      - This `def call_model` will receive the input in message and stream option and will return the response.

---

   - `def check_buffer():`
      - Checks if history exceeds the limit which will be then compacted through the compact_history function.
      - def check_buffer(): will be called each time at the end of the while 1 loop.

---

   - `def compact_history():`
      - through a summary prompt it will ask the ai to summarises its history and 
      - `summary_response = self.call_model(summary_prompt, stream=False)`
      - this summary_response will be appended to the history while deleting everything else except the system prompt(0th index of history).


## Streaming-
This was the hardest to code and had to rely on LLM to debug it because it was throwing error in lot of points in the code.
Point to be noted that the last chunk in the stream have attributes of usage-
which contains the tokens used information. 

## Try and Error blocks-
Most of the codes are enabled in try and error to not let the code to break in middle of conversation.


## ...................Getting API Key............................
Took me half and hour to debug this with gemini because somehow it was not connecting with user and showing user not found. Even after doing everystep of storing the api key in .env file storing the .env file in .gitignore the problem was something to do with whitspaces and how selecting it from somewhere to pasting it somewhere was adding something to its end as stripping was not helping. But in the end instead of copying it i hand wrote it in the file then it worked.

---
## New learning- I learned to make a readme file.



   



