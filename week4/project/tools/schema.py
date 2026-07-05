"""
Schema definitions for all available agent tools.
"""

TOOLS = [
    # ---------------------------------------------------------
    # File Operations (Week 3 ported)
    # ---------------------------------------------------------
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
    
    # ---------------------------------------------------------
    # Web & Research Tools (week 2 ported)
    # ---------------------------------------------------------
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
    },
    
    # ---------------------------------------------------------
    # Autonomous Agent Tools (week 4 Execution & Planning)
    # ---------------------------------------------------------
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Runs a shell command in the target repository. Use this to search (grep), run tests (pytest), or interact with git. Destructive or unclassified commands will pause for human approval.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The bash shell command to execute."
                    }
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_todos",
            "description": "Adds new todo items to the plan. Use this to break down the user's task into manageable steps.",
            "parameters": {
                "type": "object",
                "properties": {
                    "todos": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "description": {"type": "string"},
                                "verification_method": {"type": "string", "description": "The exact command (e.g., test command) that will prove this step is complete."}
                            },
                            "required": ["title", "description", "verification_method"]
                        }
                    }
                },
                "required": ["todos"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_todos",
            "description": "Returns the current list of todos and their statuses.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "mark_todo",
            "description": "Marks a specific todo as completed. You MUST provide evidence (like a successful test exit code) to mark a code-changing todo as complete.",
            "parameters": {
                "type": "object",
                "properties": {
                    "todo_index": {"type": "integer"},
                    "status": {"type": "string", "enum": ["completed"]},
                    "evidence": {"type": "string", "description": "Proof of completion, such as 'Exit code 0' from a test run."}
                },
                "required": ["todo_index", "status", "evidence"]
            }
        }
    }
]