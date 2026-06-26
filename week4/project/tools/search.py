import os
import ast
import re

# ... (keep existing grep and list_definitions functions) ...

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