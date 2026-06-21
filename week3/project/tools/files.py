
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

def write_file(path: str, content: str) -> dict:
    """Write content to a file, creating directories if needed."""
    try:
        abs_path = resolve_path(path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return {"content": f"Successfully wrote to {path}"}
    except Exception as e:
        return {"error": str(e)}

def edit_file(path: str, operation: str, start_line: int, end_line: int | None = None, content: str | None = None) -> dict:
    """Surgically edit a file with replace, delete, or append, returning a diff."""
    try:
        abs_path = resolve_path(path)
        with open(abs_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        start_idx = max(0, start_line - 1)
        end_idx = end_line if end_line is not None else start_line
        
        old_snippet = "".join(lines[start_idx:end_idx])
        new_lines = [line + "\n" for line in (content or "").splitlines()]

        if operation == "replace":
            lines[start_idx:end_idx] = new_lines
        elif operation == "delete":
            del lines[start_idx:end_idx]
        elif operation == "append":
            insert_pos = min(len(lines), start_idx) 
            lines[insert_pos:insert_pos] = new_lines
            old_snippet = "(Appending after line)"
        else:
            return {"error": f"Unknown operation: {operation}"}

        with open(abs_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
            
        new_snippet = "".join(new_lines) if operation != "delete" else "[DELETED]"
        diff = f"--- OLD ---\n{old_snippet}\n--- NEW ---\n{new_snippet}"
            
        return {"content": f"Successfully performed {operation}", "diff": diff}
    except Exception as e:
        return {"error": str(e)}

def list_files(path: str = ".", pattern: str = "*") -> dict:
    """List files in the workspace matching a glob pattern."""
    try:
        abs_path = resolve_path(path)
        search_path = os.path.join(abs_path, pattern)
        files = glob_module.glob(search_path, recursive=True)
        relative_files = [os.path.relpath(f, WORKSPACE_ROOT) for f in files]
        return {"files": relative_files}
    except Exception as e:
        return {"error": str(e)}
