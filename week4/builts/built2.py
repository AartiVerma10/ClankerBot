"""
Build 2: Finding Code (grep + AST Outline)
=============================================
Two tools for finding the right place in a codebase you've never seen:
search file contents by pattern, and get a structural outline of a
single file without reading the whole thing.
"""

import ast
import os
import re
import json

WORKSPACE_ROOT = os.path.abspath(os.environ.get("WORKSPACE_ROOT", "."))
MAX_GREP_RESULTS = 50
EXCLUDE_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}


def resolve_path(path: str) -> str | None:
    """Resolve `path` inside WORKSPACE_ROOT; return None if it escapes."""
    # Resolve the absolute path based on WORKSPACE_ROOT
    abs_path = os.path.abspath(os.path.join(WORKSPACE_ROOT, path))
    
    # Check if the resolved path is still strictly inside the workspace
    if not abs_path.startswith(WORKSPACE_ROOT):
        return None
    return abs_path


def grep(
    pattern: str,
    path: str = ".",
    case_sensitive: bool = False,
    max_results: int = MAX_GREP_RESULTS,
) -> dict:
    """
    Search file contents for `pattern` under `path`.

    Return: {"matches": [{"file": ..., "line": ..., "text": ...}, ...],
             "truncated": bool, "total_matches": int}

    Skip EXCLUDE_DIRS and obviously binary files. Cap at `max_results`
    but report the true total even when truncated — see Lesson 1/3.
    """
    target_path = resolve_path(path)
    if not target_path or not os.path.exists(target_path):
        return {"error": "Path is outside the workspace or does not exist."}

    flags = 0 if case_sensitive else re.IGNORECASE
    try:
        regex = re.compile(pattern, flags)
    except re.error as e:
        return {"error": f"Invalid regex pattern: {e}"}

    matches = []
    total_matches = 0

    def search_file(filepath: str):
        nonlocal total_matches
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                # 1-indexed line numbers as requested in the reading
                for line_num, line in enumerate(f, start=1):
                    if regex.search(line):
                        total_matches += 1
                        if len(matches) < max_results:
                            matches.append({
                                "file": os.path.relpath(filepath, WORKSPACE_ROOT),
                                "line": line_num,
                                "text": line.rstrip("\n")
                            })
        except UnicodeDecodeError:
            # Skip obviously binary files that fail UTF-8 decoding
            pass
        except Exception:
            # Skip files with permission errors, etc.
            pass

    if os.path.isfile(target_path):
        search_file(target_path)
    else:
        for root, dirs, files in os.walk(target_path):
            # Mutate dirs in-place to skip excluded directories
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            
            for file in files:
                search_file(os.path.join(root, file))

    return {
        "matches": matches,
        "truncated": total_matches > max_results,
        "total_matches": total_matches
    }

def list_definitions(filepath):
    """
    Parses a Python file and returns a structured list of dictionaries.
    Safely ignores non-Python files.
    """
    # 1. THE GUARD CLAUSE: Instantly skip anything that isn't a Python file
    if not filepath.endswith(".py"):
        # Return an empty list or a custom dictionary explaining it was skipped
        return [] 
        
    definitions = []
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()
        
        # Parse the source code into an Abstract Syntax Tree
        tree = ast.parse(source)
        
    except SyntaxError as e:
        # Gracefully handle files that claim to be .py but have broken syntax
        print(f"Syntax Error in {filepath}: {e}")
        return [{"error": f"SyntaxError: {e}"}]
    except Exception as e:
        # Catch any other weird file reading errors 
        print(f"Could not read {filepath}: {e}")
        return []

    # 2. Look only at the main trunk of the tree 
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            definitions.append({
                "kind": "function",
                "name": node.name,
                "line": node.lineno,
                "end_line": getattr(node, 'end_lineno', node.lineno) 
            })
            
        elif isinstance(node, ast.ClassDef):
            definitions.append({
                "kind": "class",
                "name": node.name,
                "line": node.lineno,
                "end_line": getattr(node, 'end_lineno', node.lineno)
            })
            
            for child in node.body:
                if isinstance(child, ast.FunctionDef):
                    definitions.append({
                        "kind": "method",
                        "name": child.name,
                        "line": child.lineno,
                        "end_line": getattr(child, 'end_lineno', child.lineno)
                    })
                    
    return {"definitions":definitions}

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "grep",
            "description": (
                "Search file contents for a pattern across the workspace. "
                "Use this before read_file when you don't already know which "
                "file you need."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Text or regex to search for."},
                    "path": {"type": "string", "description": "Subdirectory to search, default workspace root."},
                    "case_sensitive": {"type": "boolean", "description": "Default false."},
                    "max_results": {
                        "type": "integer",
                        "description": f"Cap on matches returned. Default {MAX_GREP_RESULTS}.",
                    },
                },
                "required": ["pattern"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_definitions",
            "description": (
                "List the functions and classes declared in a Python file, "
                "with line numbers, without reading the whole file. Use this "
                "right after grep to decide which match is worth reading in "
                "full with read_file."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to a Python file."},
                },
                "required": ["path"],
            },
        },
    },
]


if __name__ == "__main__":
    print("Searching for top-level function definitions ('def '):")
    result = grep("def ", max_results=10)
    print(json.dumps(result,indent=4))

    if result and result.get("matches"):
        first_file = result["matches"][0]["file"]
        print(f"\nOutline of {first_file}:")
        print(json.dumps(list_definitions(first_file),indent=4))