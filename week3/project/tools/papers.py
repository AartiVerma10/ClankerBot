import requests
import urllib.parse

def paper_search(query: str) -> dict:
    """Search the Hugging Face Papers database."""
    safe_query = urllib.parse.quote(query)
    url = f"https://huggingface.co/api/papers/search?q={safe_query}"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        papers = data[:5] if isinstance(data, list) else data.get("papers", [])[:5]
        return {"papers": papers}
    except Exception as e:
        return {"error": str(e)}

def read_paper(arxiv_id: str) -> dict:
    """Fetch the full markdown content of a paper using its arXiv ID."""
    url = f"https://huggingface.co/papers/{arxiv_id}.md"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return {"content": response.text[:12000]}
        return {"error": f"Paper not found. Status code: {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}