import os
import sys
from openai import OpenAI
from dotenv import load_dotenv

# if wont throw an error if the reply have any emojis
sys.stdout.reconfigure(encoding='utf-8')
load_dotenv(override=True)

class ChatAgent:
    def __init__(self, model_id, system_prompt, max_turns= 5):
        """
        Initializes the ChatAgent with a specific model, system prompt, and memory limit.
        max_turns defines how many conversational pairs (user + assistant) to keep.
        """
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

    def call_model(self, messages, stream: bool = True):
    
        api_args = {
            "model": self.model_id,
            "messages": messages,
            "stream": stream
        }
        
        
        if stream:
            api_args["stream_options"] = {"include_usage": True}

        return self.client.chat.completions.create(**api_args)
    

    def compact_history(self):
        """Summarizes the oldest messages in the history to save tokens."""
        if len(self.history) <= 4:
            print("\n[System: History too short to compact.]")
            return

        print("\n[System: Compacting memory to save tokens...]")
        messages_to_summarize = self.history[1:-2]
        
        summary_prompt = [
            {"role": "system", "content": "You are an AI memory manager. Summarize the following conversation history into a single, dense paragraph focusing on key facts, user preferences, and the core topic. Do not include pleasantries."},
            {"role": "user", "content": f"History to summarize: {str(messages_to_summarize)}"}
        ]
        
        
        try:
            summary_response = self.call_model(summary_prompt, stream=False)
            summary_text = summary_response.choices[0].message.content
            
            # Rebuild history: System Prompt -> Summary -> Latest Pair
            self.history = [
                self.history[0],
                {"role": "assistant", "content": f"[Context from earlier conversation: {summary_text}]"}
            ] + self.history[-2:]
            
            print("[System: Compaction complete.]")
        except Exception as e:
            print(f"[System Error during compaction: {e}]")

    def check_buffer(self):
        """Checks if the history exceeds max_turns and triggers compaction."""
        max_messages = (self.max_turns * 2) + 1
        if len(self.history) > max_messages:
            self.compact_history()

    def run(self):
       
        """The main interactive chat loop."""
        print(f"\n\n--- Chat Agent Started [{self.model_id}] ---")
        print()
        print("""You can perform the following functions:
        . Talk with it (it lacks friends, so do i)
        . No other option just talk with it. hehe.
        . Type 'exit' or 'quit' to kill it.(this will kill its memory too. sad.)
        . Type '/reset' to erase all its memory (sad again.)
        . Type '/tokens' to get information of the tokens used.
        . Type '/compact' to force summarize its memory.""")
        
        while True:
            user_input = input("\nYou: ")
            
         
            if user_input.lower() in ['exit', 'quit']:
                
                temp_history = self.history + [{"role": "user", "content": "i want to end this conversation now, bye. say something dramatic before shutting down."}]
                
                print("\nAI: ", end="", flush=True)

                try:
                    response_stream = self.call_model(temp_history, stream=True)
                    for chunk in response_stream:
                        if len(chunk.choices) > 0 and chunk.choices[0].delta.content:
                            print(chunk.choices[0].delta.content, end="", flush=True)
                except Exception as e:
                    print(f"[Error: {e}]")
                
                print("\n\n[System: Chat session terminated.]")
                break
                
          
            elif user_input.lower() == '/compact':
                self.compact_history()
                continue
            
        
            elif user_input.lower() == '/reset':
                
                temp_history = self.history + [{"role": "user", "content": "i am wiping your memory right now. give a sarcastic or dramatic final response before you forget everything."}]
                
                print("\nAI: ", end="", flush=True)
                try:
                    response_stream = self.call_model(temp_history, stream=True)
                    for chunk in response_stream:
                        if len(chunk.choices) > 0 and chunk.choices[0].delta.content:
                            print(chunk.choices[0].delta.content, end="", flush=True)
                except Exception as e:
                    print(f"[Error: {e}]")

                
                self.history = [{"role": "system", "content": self.system_prompt}]
                self.last_usage = None
                print("\n\n[System: Memory Erased!]")
                continue

        
            elif user_input.lower() == '/tokens':
                if self.last_usage:
                    print(f"\nTokens Used in last message - Prompt: {self.last_usage.prompt_tokens}, Completion: {self.last_usage.completion_tokens}, Total: {self.last_usage.total_tokens}")
                else:
                    print("\nNo tokens used yet. Talk to me first!")
                continue
          
          
            self.history.append({"role": "user", "content": user_input})
            print("\nAI: ", end="", flush=True)
            
            try:
                response_stream = self.call_model(self.history, stream=True)
                full_reply = ""
                
                for chunk in response_stream:
                    # Print tokens as they stream in
                    if len(chunk.choices) > 0 and chunk.choices[0].delta.content:
                        token = chunk.choices[0].delta.content
                        print(token, end="", flush=True)
                        full_reply += token
                    
                    # Intercept the usage data which comes at the very end of the stream
                    if hasattr(chunk, 'usage') and chunk.usage is not None:
                        self.last_usage = chunk.usage
                
                print() 
                
                self.history.append({"role": "assistant", "content": full_reply})
                self.check_buffer()
                
            except Exception as e:
                print(f"\n[Error communicating with API: {e}]")
                self.history.pop()

def setup():
    """Handles configuration and model selection before starting the agent."""
    print("\n\nWelcome to the Multi-Model ChatAgent Interface\n")
    print("---------------------------------------------")
    print("\nAvailable Models:")
    print("1. deepseek/deepseek-chat")
    print("2. openai/gpt-3.5-turbo")
    print("3. anthropic/claude-3-haiku")
    print("4. Custom ID")
    
    choice = input("\nSelect a model (1-4): ")
    
    models = {
        "1": "deepseek/deepseek-chat",
        "2": "openai/gpt-3.5-turbo",
        "3": "anthropic/claude-3-haiku"
    }
    
    if choice in models:
        selected_model = models[choice]
    elif choice == "4":
        selected_model = input("Enter the OpenRouter Model ID: ")
    else:
        print("Invalid choice, defaulting to deepseek/deepseek-chat")
        selected_model = "deepseek/deepseek-chat"

    
    exact_system_prompt = "You are a sarcastic but helpful assistant. Act like a gen alpha teen, talk in brainrot, be extremely harsh or toxic/sarcastic, but talk in shakespear kind of english, but simple and also talk in gang language like gang,chat,twin type shit ok. Always reply in all lowercase letters and use at least one emoji."
    

    my_agent = ChatAgent(
        model_id=selected_model,
        system_prompt=exact_system_prompt,
        max_turns=3 # Compaction buffer size
    )

    my_agent.run()

if __name__ == "__main__":
    setup()
