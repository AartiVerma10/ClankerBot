import os
import subprocess
import threading
import time
from tools.safety import request_approval

SAFE_COMMANDS = ["ls", "cat", "grep", "find", "pwd", "echo", "git status", "git log", "git diff", "pytest"]
SLOW_COMMANDS = ["pytest", "npm install", "pip install", "docker build", "apt-get"]

BACKGROUND_JOBS = {}
COMPLETED_JOBS = {}
JOB_COUNTER = 1

os.makedirs(".agent", exist_ok=True)

def _job_monitor():
    """Daemon thread that polls background jobs silently."""
    while True:
        for job_id, process in list(BACKGROUND_JOBS.items()):
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                COMPLETED_JOBS[job_id] = {
                    "exit_code": process.returncode,
                    "stdout": stdout,
                    "stderr": stderr
                }
                del BACKGROUND_JOBS[job_id]
        time.sleep(1)

threading.Thread(target=_job_monitor, daemon=True).start()

def run_command(command: str, timeout: int = 30) -> str:
    global JOB_COUNTER
    
    is_safe = any(command.strip().startswith(cmd) for cmd in SAFE_COMMANDS)
    if not is_safe:
        if not request_approval("Destructive/Unclassified Command", f"Command: {command}"):
            return "Command execution cancelled by user."

    is_slow = any(slow in command for slow in SLOW_COMMANDS)
    
    if is_slow:
        print(f"\n\033[96m[Running long command: '{command}' - Press Ctrl+C to interrupt/background]\033[0m")
        try:
            process = subprocess.Popen(
                command, 
                shell=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True
            )
            
            while process.poll() is None:
                time.sleep(0.5)
                
            stdout, stderr = process.communicate()
            return f"Exit Code: {process.returncode}\nStdout:\n{stdout}\nStderr:\n{stderr}\n"
            
        except KeyboardInterrupt:
            print(f"\n\033[93m\n⚠️ Execution Interrupted!\033[0m")
            while True:
                choice = input("\033[1mMove task to [b]ackground or [c]ancel it? [b/c]: \033[0m").strip().lower()
                if choice in ('b', 'background'):
                    job_id = JOB_COUNTER
                    BACKGROUND_JOBS[job_id] = process
                    JOB_COUNTER += 1
                    return f"System Note: The command '{command}' was interrupted by the user and moved to the background with Job ID {job_id}. The agent should continue with other tasks."
                elif choice in ('c', 'cancel'):
                    process.terminate()
                    return "Command execution cancelled by user."
    else:
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=timeout)
            return f"Exit Code: {result.returncode}\nStdout:\n{result.stdout}\nStderr:\n{result.stderr}\n"
        except subprocess.TimeoutExpired:
            return f"Error: Command timed out after {timeout} seconds."
        except Exception as e:
            return f"Error executing command: {str(e)}"

def check_background_job(job_id: int) -> str:
    """Checks the status of a background job and retrieves its output if done."""
    if job_id in COMPLETED_JOBS:
        data = COMPLETED_JOBS.pop(job_id)
        output = f"Job {job_id} Finished. Exit Code: {data['exit_code']}\n"
        if data['stdout']: output += f"Stdout:\n{data['stdout']}\n"
        if data['stderr']: output += f"Stderr:\n{data['stderr']}\n"
        return output
        
    if job_id in BACKGROUND_JOBS:
        return f"Job {job_id} is still running in the background."
        
    return f"Error: No background job found with ID {job_id}."