import sys
import time
import os
import difflib

# ANSI Color Codes
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"

def get_colorized_diff(original_text: str, new_text: str, filename: str) -> str:
    """Generate a standard unified diff and colorize it for the terminal."""
    original_lines = original_text.splitlines(keepends=True)
    new_lines = new_text.splitlines(keepends=True)
    
    diff = difflib.unified_diff(
        original_lines, new_lines, 
        fromfile=f"a/{filename}", tofile=f"b/{filename}", n=3
    )
    
    colorized = []
    for line in diff:
        if line.startswith("+") and not line.startswith("+++"):
            colorized.append(f"{GREEN}{line}{RESET}")
        elif line.startswith("-") and not line.startswith("---"):
            colorized.append(f"{RED}{line}{RESET}")
        elif line.startswith("@@"):
            colorized.append(f"{YELLOW}{line}{RESET}")
        else:
            colorized.append(line)
            
    return "".join(colorized)

def request_approval(action_type: str, details: str, diff: str = None) -> bool:
    """Pause execution, print a warning (with optional diff), and ask the user for y/n."""
    print(f"\n{YELLOW}{BOLD}⚠️  AGENT REQUIRES APPROVAL: {action_type}{RESET}")
    print("-" * 50)
    
    if diff:
        print(diff)
    else:
        print(f"{RED}{details}{RESET}")
        
    print("-" * 50)
    
    sys.stdout.flush()
    while True:
        choice = input(f"{BOLD}Allow this action? [y/N]: {RESET}").strip().lower()
        if choice in ('y', 'yes'):
            return True
        if choice in ('n', 'no', ''):
            return False

def prompt_background_task(task_name: str, estimated_time: str = "Unknown") -> str:
    """Prompt the user to run a long task in the background, append it, or cancel."""
    print(f"\n{CYAN}{BOLD}⏳ LONG-RUNNING TASK PREVIEW: {task_name}{RESET}")
    print("-" * 50)
    print(f"The agent wants to run a task that may take some time (Est: {estimated_time}).")
    print(f"How would you like to proceed?")
    print(f"  [{GREEN}b{RESET}] Run in background (agent continues working)")
    print(f"  [{GREEN}a{RESET}] Append to queue (skip for now, do it later)")
    print(f"  [{RED}c{RESET}] Cancel this task completely")
    print("-" * 50)
    
    sys.stdout.flush()
    while True:
        choice = input(f"{BOLD}Select action [b/a/c]: {RESET}").strip().lower()
        
        if choice in ('b', 'background'):
            return 'background'
        elif choice in ('a', 'append'):
            return 'append'
        elif choice in ('c', 'cancel', 'n', 'no'):
            return 'cancel'
        else:
            print(f"{YELLOW}Invalid input. Please enter 'b', 'a', or 'c'.{RESET}")

# Update log_notification in tools/safety.py

def log_notification(message: str, session_id: str = None, session_title: str = None) -> None:
    """Writes a timestamped message to the notification log, tracking the session."""
    import os
    import time
    os.makedirs(".agent", exist_ok=True)
    with open(".agent/notifications.log", "a", encoding="utf-8") as f:
        timestamp = time.strftime("%H:%M:%S")
        clean_message = message.replace('\n', ' ').strip()
        
        # Add a clean session tag combining title and ID if provided
        if session_id and session_title:
            session_tag = f"[Session: {session_title} ({session_id})] "
        elif session_id:
            session_tag = f"[Session: {session_id}] "
        else:
            session_tag = ""
            
        f.write(f"[{timestamp}] {session_tag}{clean_message}\n")