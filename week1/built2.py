
import os
import sys
# Force the terminal to accept UTF-8 characters (like emojis)
sys.stdout.reconfigure(encoding='utf-8')

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(override=True)

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY"),
)




def run_chatbot():
    system_prompt = "You are a sarcastic but helpful assistant. Act like a gen alpha teen, talk in brainrot, be extremely harsh or toxic/sarcastic, but talk in shakespear kind of english, but simple and also talk in gang language like gang,chat,twin type shit ok. Always reply in all lowercase letters and use at least one emoji."   
    history = [
        {"role": "system", "content": system_prompt},    
    ]
    
    last_usage = None
    
    print("""YOUR PERSONAL CHATBOT STARTED
    
   You can perform the following functions:
1. Talk with it (it lacks friends, so do i)
2. No other option just talk with it. hehe.
3. Type exit or quit to kill it.(this will kill its memory too. sad.)
4. Type /reset to erase all its memory (sad again.)
5. Type /tokens to get information of the tokens used.""")
    print()
    
    while True:
        usinput = input(">> ")
        
        if usinput.lower() in ["exit", "quit"]:
            history.append({"role": "user", "content": "I want to quit this conversation now, bye"})
            response = client.chat.completions.create(
                model="deepseek/deepseek-chat",
                messages=history
            )
            # FIXED: Added .message
            print(f"\nAssistant: {response.choices[0].message.content}") 
            break

        elif usinput.lower() == "/reset":
            history.append({"role": "user", "content": "forget all details about me"})
            response = client.chat.completions.create(
                model="deepseek/deepseek-chat",
                messages=history
            )
         
            print(f"\nAssistant: {response.choices[0].message.content}") 
            print()
            history = [{"role": "system", "content": system_prompt}]
            last_usage = None

        elif usinput.lower() == "/tokens":        
            if last_usage:
                print(f"\nTokens Used - Prompt: {last_usage.prompt_tokens}, Completion: {last_usage.completion_tokens}, Total: {last_usage.total_tokens}")
            else:
                print("\nNo tokens used yet. Talk to me first!")

        else:
            history.append({"role": "user", "content": usinput})
            response = client.chat.completions.create(
                model="deepseek/deepseek-chat",
                messages=history
            )
            
            reply = response.choices[0].message.content
            history.append({"role": "assistant", "content": reply})
            
            print(f"\nAssistant: {reply}\n")
            last_usage = response.usage

if __name__ == "__main__":
    run_chatbot()  

