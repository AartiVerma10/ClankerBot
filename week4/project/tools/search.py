import os
import ast
import re

# ... (keep existing grep and list_definitions functions) ...

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


def list_definitions(path: str) -> dict:
    """
    Parse a Python file with `ast` and return every function/class it
    declares, in source order, with line numbers — a structural outline
    without reading the file's full body.
    """
    target_path = resolve_path(path)
    if not target_path or not os.path.isfile(target_path):
        return {"error": "File not found or path escapes sandbox."}

    try:
        with open(target_path, "r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source, filename=os.path.basename(target_path))
    except SyntaxError as e:
        return {"error": f"SyntaxError parsing file: {e}"}
    except Exception as e:
        return {"error": str(e)}

    definitions = []

    # Walk the top-level body of the AST
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            definitions.append({
                "kind": "function",
                "name": node.name,
                "line": node.lineno,
                "end_line": getattr(node, "end_lineno", node.lineno)
            })
        elif isinstance(node, ast.AsyncFunctionDef):
            definitions.append({
                "kind": "async function",
                "name": node.name,
                "line": node.lineno,
                "end_line": getattr(node, "end_lineno", node.lineno)
            })
        elif isinstance(node, ast.ClassDef):
            definitions.append({
                "kind": "class",
                "name": node.name,
                "line": node.lineno,
                "end_line": getattr(node, "end_lineno", node.lineno)
            })
            
            # If it's a class, walk its body for methods so the caller 
            # sees structure without a second tool call.
            for subnode in node.body:
                if isinstance(subnode, ast.FunctionDef):
                    definitions.append({
                        "kind": "method",
                        "name": subnode.name,
                        "line": subnode.lineno,
                        "end_line": getattr(subnode, "end_lineno", subnode.lineno)
                    })
                elif isinstance(subnode, ast.AsyncFunctionDef):
                    definitions.append({
                        "kind": "async method",
                        "name": subnode.name,
                        "line": subnode.lineno,
                        "end_line": getattr(subnode, "end_lineno", subnode.lineno)
                    })

    return {"definitions": definitions}



def get_repo_map(max_files: int = 15) -> dict:
    """
    Builds a structural map of the repo by finding all definitions, 
    counting their cross-references, and returning the most important files.
    """
    all_py_files = []
    for root, dirs, files in os.walk(WORKSPACE_ROOT):
        dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "venv", "__pycache__"}]
        for file in files:
            if file.endswith(".py"):
                all_py_files.append(os.path.join(root, file))

    file_outlines = {}
    all_symbols = set()

    # Step 1: Parse every file for definitions
    for filepath in all_py_files:
        rel_path = os.path.relpath(filepath, WORKSPACE_ROOT)
        outline = list_definitions(rel_path)
        if "definitions" in outline:
            file_outlines[rel_path] = outline["definitions"]
            for df in outline["definitions"]:
                # Ignore dunder methods like __init__ for ranking
                if not df["name"].startswith("__"):
                    all_symbols.add(df["name"])

    # Step 2: Crude PageRank / Reference counting
    file_scores = {path: 0 for path in file_outlines}
    
    for filepath in all_py_files:
        rel_path = os.path.relpath(filepath, WORKSPACE_ROOT)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                # Count occurrences of every known symbol
                for symbol in all_symbols:
                    # Very basic exact word match
                    hits = len(re.findall(rf'\b{re.escape(symbol)}\b', content))
                    if hits > 0:
                        file_scores[rel_path] += hits
        except Exception:
            continue

    # Step 3: Sort by score and cap the budget
    ranked_files = sorted(file_scores.keys(), key=lambda k: file_scores[k], reverse=True)
    top_files = ranked_files[:max_files]

    budget_capped_map = {
        file: file_outlines[file] for file in top_files
    }

    return {
        "message": f"Repo map generated. Showing top {max_files} most referenced files.",
        "repo_map": budget_capped_map
    }