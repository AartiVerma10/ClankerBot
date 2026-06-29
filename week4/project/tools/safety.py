import sys
import difflib

# ANSI Color Codes
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
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
    
    # Flush stdin to prevent accidental rapid 'y' presses carrying over
    sys.stdout.flush()
    while True:
        choice = input(f"{BOLD}Allow this action? [y/N]: {RESET}").strip().lower()
        if choice in ('y', 'yes'):
            return True
        if choice in ('n', 'no', ''):
            return False