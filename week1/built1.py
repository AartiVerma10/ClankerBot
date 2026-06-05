import os
import sys

# Force the terminal to accept UTF-8 characters (like emojis)
sys.stdout.reconfigure(encoding='utf-8')

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client=OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY"),
)



def call_model(prompt: str, fla: int) -> str:
    response=client.chat.completions.create(
        model="deepseek/deepseek-chat",
        messages=[
            {"role": "system", "content": "You are a sarcastic but helpful assistant. Act like a gen alpha teen, talk in brainrot, be extremely harsh or toxic/sarcastic, but talk in shakespear kind of english, but simple and also talk in gang language like gang,chat,twin type shit ok. Always reply in all lowercase letters and use at least one emoji."},
            {"role": "user","content": prompt}
        ],
    )
    
    if fla==1:
        print("\n--- DEBUG: RAW RESPONSE OBJECT ---")
        print(response.model_dump_json(indent=2)) 
        print("----------------------------------\n")
        print(f"Tokens Used - Prompt: {response.usage.prompt_tokens}, "
            f"Completion: {response.usage.completion_tokens}, "
            f"Total: {response.usage.total_tokens}\n")
        print(f"Finish Reason: {response.choices[0].finish_reason}\n")

    return response.choices[0].message.content

if __name__=="__main__":
    print("--------------------------")
    print(">>>mirror, mirror on the wall, who's the prettiest of them all?" )
    print("--------------------------")
    print(call_model("mirror, mirror on the wall, who's the prettiest of them all? ",0))
    print("--------------------------")
    print(">>>i dont have friends, m sad")
    print("--------------------------")
    print(call_model("i dont have friends, m sad",0))
    print("--------------------------")