import json
from tools.safety import log_notification

_plan_state = {
    "session_id": "Unknown",
    "session_title": "Unknown", # <-- Track title as well
    "todos": []
}

def set_active_session(session_id: str, session_title: str = "Untitled") -> None:
    """Links the current plan to the active session ID and Title."""
    _plan_state["session_id"] = session_id
    _plan_state["session_title"] = session_title

# ... [keep add_todos and get_todos unchanged] ...
def add_todos(todos: list[dict]) -> str:
    """Adds new todo items to the plan. Each todo should have a 'title', 'description', and 'verification_method'."""
    for todo in todos:
        todo['status'] = 'pending'
        todo['evidence'] = None
        _plan_state["todos"].append(todo)
    return "Todos successfully added to the plan."

def get_todos() -> str:
    """Returns the current list of todos and their statuses."""
    if not _plan_state["todos"]:
        return "No todos in the current plan."
    return json.dumps(_plan_state["todos"], indent=2)



def mark_todo(todo_index: int, status: str, evidence: str) -> str:
    """Marks a specific todo and logs a notification with the session title and ID."""
    try:
        todo = _plan_state["todos"][todo_index]
        if status == "completed" and not evidence:
            return "Error: Cannot mark a todo as completed without verification evidence."
            
        todo["status"] = status
        todo["evidence"] = evidence
        
        log_message = f"Task Update: '{todo['title']}' is now {status}. Remarks: {evidence}"
        
        # Pass both ID and Title to the logger
        log_notification(
            log_message, 
            session_id=_plan_state["session_id"],
            session_title=_plan_state["session_title"]
        )
        
        return f"Todo {todo_index} marked as {status}."
    except IndexError:
        return "Error: Invalid todo index."