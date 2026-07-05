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
            "name": "check_background_job",
            "description": "Checks the status of a background job using its Job ID. Use this to verify if a long-running command has finished and retrieve its output.",
            "parameters": {
                "type": "object",
                "properties": {
                    "job_id": {
                        "type": "integer",
                        "description": "The integer Job ID returned when the command was started."
                    }
                },
                "required": ["job_id"]
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
    },
    {
        "type": "function",
        "function": {
            "name": "grep",
            "description": "Search for a regex pattern across files in the workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "The regex pattern to search for."},
                    "path": {"type": "string", "description": "Optional specific directory or file to search within."}
                },
                "required": ["pattern"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_definitions",
            "description": "Outline a Python file by listing its classes, functions, and methods.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "The relative path to the Python file."}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_repo_map",
            "description": "Builds a structural map of the repository showing the most referenced files and their definitions. Use this when exploring an unfamiliar codebase.",
            "parameters": {
                "type": "object",
                "properties": {
                    "max_files": {"type": "integer", "description": "Maximum number of top referenced files to return (default is 15)."}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delegate_exploration",
            "description": "Spins up a read-only subagent to thoroughly explore the codebase and answer a broad question. Returns a dense, formatted digest citing files and line numbers.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_description": {"type": "string", "description": "Detailed instructions on what the subagent needs to find or understand."}
                },
                "required": ["task_description"]
            }
        }
    }
]