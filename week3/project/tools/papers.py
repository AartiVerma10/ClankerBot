import json
import requests
import urllib.parse 
import re
from tools.web import web_fetch 

def paper_search(query: str) -> dict:
    """Search the Hugging Face Papers database."""
    safe_query = urllib.parse.quote(query)
    url = f"https://huggingface.co/api/papers?q={safe_query}"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        papers = data[:5] if isinstance(data, list) else data.get("papers", [])[:5]
        return {"papers": papers}
    except Exception as e:
        return {"error": str(e)}    

def read_paper(arxiv_id: str) -> dict:
    """Fetch paper content, with a web fallback to arXiv."""
    
    # 1. Normalize the ID (Strips URLs, 'arxiv:' prefixes, and 'v1' suffixes)
    clean_id = re.sub(r'^(?:https?://arxiv\.org/abs/|arxiv:)', '', arxiv_id, flags=re.IGNORECASE)
    clean_id = re.sub(r'v\d+$', '', clean_id)
    
    try:
        url = f"https://huggingface.co/api/papers/{clean_id}"
        hf_response = requests.get(url, timeout=10)
        
        if hf_response.status_code == 404:
            raise FileNotFoundError("HF returned 404")
            
        data = hf_response.json()
        title = data.get("title", "Unknown Title")
        summary = data.get("summary", "No summary available.")
        
        content = f"# {title}\n\n## Abstract\n{summary}"
        
        # 2. Truncate to save tokens (Max 10,000 characters)
        if len(content) > 10000:
            content = content[:10000] + "\n...[TRUNCATED]"
            
        return {"content": content} 
        
    except Exception as e:
        print(f"\n[Fallback] HF Paper failed. Fetching directly from arXiv...")
        fallback_url = f"https://arxiv.org/abs/{clean_id}"
        fallback_text = web_fetch(fallback_url)
        
        # Truncate fallback text too
        if len(fallback_text) > 10000:
            fallback_text = fallback_text[:10000] + "\n...[TRUNCATED]"
            
        return {"content": f"Full paper unavailable. Abstract from ArXiv:\n{fallback_text}"}
