import os
import shlex
import subprocess

WORKSPACE_ROOT = os.path.abspath(os.environ.get("WORKSPACE_ROOT", "."))
TIMEOUT_DEFAULT = 10
MAX_OUTPUT_CHARS = 8_000

# Known-safe: run immediately once the path check passes.
READ_ONLY_PREFIXES = (
    "grep", "find", "ls", "cat", "head", "tail", "wc",
    "git log", "git diff", "git status", "git blame", "git show",
    "pytest", "python -m pytest", "ruff", "flake8", "mypy",
)

# Known-destructive: always ask, even if they'd otherwise look harmless.
DESTRUCTIVE_PATTERNS = (
    "rm ", "mv ", ">", ">>", "git commit", "git push", "git checkout --",
    "pip install", "npm install", "curl ", "sudo ", "chmod ",
)


def paths_within_sandbox(command: str, workspace_root: str) -> bool:
    """
    Token-level check: no path-looking argument in `command` may resolve
    outside `workspace_root`.
    """
    try:
        tokens = shlex.split(command)
    except ValueError:
        return False
        
    real_workspace = os.path.realpath(workspace_root)
    
    for token in tokens:
        if token.startswith("-"):
            continue
            
        if os.path.isabs(token):
            if not os.path.realpath(token).startswith(real_workspace):
                return False
        else:
            resolved = os.path.realpath(os.path.join(real_workspace, token))
            if not resolved.startswith(real_workspace):
                return False
                
    return True


def classify_command(command: str) -> str:
    """
    Return "read_only" if `command` matches a known-safe prefix and no
    destructive pattern, otherwise "ask".
    """
    cmd_stripped = command.strip()
    
    for pattern in DESTRUCTIVE_PATTERNS:
        if pattern in cmd_stripped:
            return "ask"
            
    for prefix in READ_ONLY_PREFIXES:
        if cmd_stripped == prefix or cmd_stripped.startswith(prefix + " "):
            return "read_only"
            
    return "ask"


def run_command(command: str, cwd: str = WORKSPACE_ROOT, timeout: int = TIMEOUT_DEFAULT) -> dict:
    """
    Run a shell command, sandboxed to `cwd`, and return a structured dictionary
    including stdout, stderr, the exit_code, and a truncation boolean.
    """
    if not paths_within_sandbox(command, cwd):
        return {
            "stdout": "",
            "stderr": f"Command rejected: Contains paths outside '{cwd}'.",
            "exit_code": 1,
            "truncated": False
        }
        
    classification = classify_command(command)
    
    if classification == "ask":
        print(f"\nWARNING: Destructive or unrecognized command requested.")
        print(f"Command: `{command}`")
        choice = input("Allow execution? (y/n): ").strip().lower()
        if choice != 'y':
            return {
                "stdout": "",
                "stderr": "Execution declined by human operator.",
                "exit_code": 1,
                "truncated": False
            }
            
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            cwd=cwd, 
            timeout=timeout, 
            capture_output=True, 
            text=True
        )
        
        stdout = result.stdout
        stderr = result.stderr
        was_truncated = False
        
        # Check standard output truncation (1x Max)
        if len(stdout) > MAX_OUTPUT_CHARS:
            stdout = stdout[:MAX_OUTPUT_CHARS] + f"\n\n[SYSTEM WARNING: Output truncated. Showing first {MAX_OUTPUT_CHARS} chars.]"
            was_truncated = True
            
        # Check standard error truncation (1.5x Max)
        max_stderr_chars = 1.5 * MAX_OUTPUT_CHARS
        if len(stderr) > max_stderr_chars:
            stderr = stderr[:max_stderr_chars] + f"\n\n[SYSTEM WARNING: Error output truncated. Showing first {max_stderr_chars} chars.]"
            was_truncated = True
            
        return {
            "stdout": stdout,
            "stderr": stderr,
            "exit_code": result.returncode,
            "truncated": was_truncated
        }
        
    except subprocess.TimeoutExpired as e:
        stdout = e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
        stderr = e.stderr.decode() if isinstance(e.stderr, bytes) else (e.stderr or "")
        was_truncated = False
        
        if len(stdout) > MAX_OUTPUT_CHARS:
            stdout = stdout[:MAX_OUTPUT_CHARS] + f"\n\n[SYSTEM WARNING: Output truncated.]"
            was_truncated = True
            
        max_stderr_chars = 2 * MAX_OUTPUT_CHARS
        if len(stderr) > max_stderr_chars:
            stderr = stderr[:max_stderr_chars] + f"\n\n[SYSTEM WARNING: Error output truncated.]"
            was_truncated = True
            
        # Append timeout context to stderr to explicitly explain the exit code
        stderr += f"\n\n[SYSTEM ERROR: Command timed out after {timeout} seconds.]"
            
        return {
            "stdout": stdout,
            "stderr": stderr,
            "exit_code": 124, # Standard exit code for timeout
            "truncated": was_truncated
        }
    except Exception as e:
        return {
            "stdout": "",
            "stderr": f"Execution failed: {str(e)}",
            "exit_code": 1,
            "truncated": False
        }


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": (
                "Run a shell command in the workspace and return its output. "
                "Use this to search (grep/find), inspect history (git log/diff), "
                "run tests, or run linters. Read-only commands run immediately. "
                "Commands that write, delete, or install will pause and ask the "
                "human operator for approval before running — expect that pause, "
                "don't treat it as a failure."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The shell command to run.",
                    },
                    "timeout": {
                        "type": "integer",
                        "description": f"Seconds before the command is killed. Default {TIMEOUT_DEFAULT}.",
                    },
                },
                "required": ["command"],
            },
        },
    }
]



if __name__ == "__main__":
    print("Read-only command (should run immediately):")
    print(run_command("cat built1.py"))

    print("\nDestructive command (should pause and ask for approval):")
    print(run_command("rm -rf /tmp/does-not-exist-example"))

    