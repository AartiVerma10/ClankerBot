import os
import glob 
from tools.safety import request_approval, get_colorized_diff

WORKSPACE_ROOT = os.path.abspath(os.environ.get("WORKSPACE_ROOT", "."))
MAX_READ_CHARS = 10000 # <-- Add this limit so big files don't crash the LLM




def resolve_path(path: str) -> str:
    """Ensure path is within WORKSPACE_ROOT and return absolute path."""
    full_path = os.path.normpath(os.path.join(WORKSPACE_ROOT, path))
    if not full_path.startswith(os.path.abspath(WORKSPACE_ROOT)):
        raise PermissionError(f"Access denied: {path} is outside the workspace.")
    return full_path

# --- The Safety Gate ---
def ask_permission(action: str, path: str) -> bool:
    """Safety gate for destructive actions."""
    print(f"\n[🛡️ SAFETY GATE] The AI wants to {action} -> {path}")
    choice = input("Allow? (y/n): ").strip().lower()
    return choice == 'y'

def read_file(path: str, start_line: int = 1, read_lines: int = 200) -> dict:
    """Read lines from a file with line numbers prepended."""
    try:
        abs_path = resolve_path(path)
        with open(abs_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        start_idx = max(0, start_line - 1)
        end_idx = start_idx + read_lines
        
        numbered_lines = []
        for i, line in enumerate(lines[start_idx:end_idx]):
            numbered_lines.append(f"{start_idx + i + 1}| {line.rstrip()}")
            
        content = "\n".join(numbered_lines)
        has_more = end_idx < len(lines)
        
        if len(content) > MAX_READ_CHARS:
            content = content[:MAX_READ_CHARS] + "\n...[truncated]"
            
        return {"content": content, "total_lines": len(lines), "has_more": has_more}
    except Exception as e:
        return {"error": str(e)}
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


def list_files(path: str = ".", pattern: str = "*") -> dict:
    """List files in the workspace matching a glob pattern."""
    try:
        abs_path = resolve_path(path)
        search_path = os.path.join(abs_path, pattern)
        files = glob.glob(search_path, recursive=True)
        relative_files = [os.path.relpath(f, WORKSPACE_ROOT) for f in files]
        return {"files": relative_files}
    except Exception as e:
        return {"error": str(e)}