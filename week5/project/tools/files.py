import os
from tools.safety import request_approval, get_colorized_diff

WORKSPACE_ROOT = os.path.abspath(os.environ.get("WORKSPACE_ROOT", "."))

# ... (keep read_file and list_files as they were) ...

def write_file(path: str, content: str) -> dict:
    abs_path = os.path.abspath(os.path.join(WORKSPACE_ROOT, path))
    if not abs_path.startswith(WORKSPACE_ROOT):
        return {"error": "Path escapes sandbox."}

    original_text = ""
    if os.path.exists(abs_path):
        with open(abs_path, "r", encoding="utf-8") as f:
            original_text = f.read()

    # Generate diff and ask for approval
    diff = get_colorized_diff(original_text, content, os.path.basename(path))
    if not request_approval("WRITE FILE", f"Target: {path}", diff=diff):
        return {"error": "Action blocked: User denied file write."}

    with open(abs_path, "w", encoding="utf-8") as f:
        f.write(content)
    return {"success": True, "message": f"Successfully wrote {path}"}

def edit_file(path: str, search_text: str, replacement_text: str) -> dict:
    abs_path = os.path.abspath(os.path.join(WORKSPACE_ROOT, path))
    if not abs_path.startswith(WORKSPACE_ROOT):
        return {"error": "Path escapes sandbox."}
        
    if not os.path.exists(abs_path):
        return {"error": "File not found."}

    with open(abs_path, "r", encoding="utf-8") as f:
        original_text = f.read()

    if search_text not in original_text:
        return {"error": "Search text not found in file."}

    new_text = original_text.replace(search_text, replacement_text, 1)

    # Generate diff and ask for approval
    diff = get_colorized_diff(original_text, new_text, os.path.basename(path))
    if not request_approval("EDIT FILE", f"Target: {path}", diff=diff):
        return {"error": "Action blocked: User denied file edit."}

    with open(abs_path, "w", encoding="utf-8") as f:
        f.write(new_text)
    return {"success": True, "message": f"Successfully edited {path}"}