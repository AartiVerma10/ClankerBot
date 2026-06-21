
# --- Tool Registry ---

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file from the workspace",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "start_line": {"type": "integer"},
                    "read_lines": {"type": "integer"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"}
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": "Surgically edit a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "operation": {"type": "string", "enum": ["replace", "delete", "append"]},
                    "start_line": {"type": "integer"},
                    "end_line": {"type": "integer"},
                    "content": {"type": "string"}
                },
                "required": ["path", "operation", "start_line"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files in workspace",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "pattern": {"type": "string"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for current information.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_fetch",
            "description": "Fetch the content of a specific URL.",
            "parameters": {
                "type": "object",
                "properties": {"url": {"type": "string"}},
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "paper_search",
            "description": "Search Hugging Face for academic papers.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_paper",
            "description": "Read the full markdown content of a paper using its arXiv ID.",
            "parameters": {
                "type": "object",
                "properties": {"arxiv_id": {"type": "string"}},
                "required": ["arxiv_id"]
            }
        }
    }
]

