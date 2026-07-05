import subprocess
import shlex
import os
# Assuming you move request_approval to a shared location like safety.py or import it from agent
from safety import request_approval 

# A simple list of safe, read-only commands
SAFE_COMMANDS = ["ls", "cat", "grep", "find", "pwd", "echo", "git status", "git log", "git diff", "pytest"]

def run_command(command: str, timeout: int = 30) -> str:
    """Runs a shell command in the target repository."""
    
    # 1. Classification & Safety Gate
    is_safe = any(command.strip().startswith(cmd) for cmd in SAFE_COMMANDS)
    
    if not is_safe:
        approved = request_approval(
            action_type="Destructive or Unclassified Command",
            details=f"Command to execute: {command}"
        )
        if not approved:
            return "Command execution cancelled by user."

    # 2. Execution (with Sandboxing / Path Checking logic placeholder)
    try:
        # Note: In a real implementation, you'd enforce the cwd to be target_repo/
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        output = f"Exit Code: {result.returncode}\n"
        if result.stdout:
            output += f"Stdout:\n{result.stdout}\n"
        if result.stderr:
            output += f"Stderr:\n{result.stderr}\n"
            
        return output

    except subprocess.TimeoutExpired:
        return f"Error: Command timed out after {timeout} seconds."
    except Exception as e:
        return f"Error executing command: {str(e)}"