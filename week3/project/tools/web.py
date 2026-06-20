import os
import json
import requests

def web_search(query: str) -> dict:
    """Search the web using Google Serper."""
    url = "https://google.serper.dev/search"
    payload = json.dumps({"q": query})
    headers = {
        'X-API-KEY': os.environ.get("SERPER_API_KEY", ""), 
        'Content-Type': 'application/json'
    }
    try:
        response = requests.post(url, headers=headers, data=payload, timeout=10)
        return {"results": response.json().get("organic", [])[:5]}
    except Exception as e:
        return {"error": str(e)}

def web_fetch(url: str) -> dict:
    """Fetch and read a webpage, truncating to save context window."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        return {"content": response.text[:12000]}
    except Exception as e:
        return {"error": str(e)}