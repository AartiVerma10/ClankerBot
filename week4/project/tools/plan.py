import json

# Simple in-memory state for the current session's plan
# In a robust implementation, this might be saved to a file in .agent/sessions/
_plan_state = {
    "todos": []
}

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
    """
    Marks a specific todo as 'completed'. 
    Requires evidence (like an exit code 0 from a test) to be accepted.
    """
    try:
        todo = _plan_state["todos"][todo_index]
        if status == "completed" and not evidence:
            return "Error: Cannot mark a todo as completed without verification evidence."
            
        todo["status"] = status
        todo["evidence"] = evidence
        return f"Todo {todo_index} marked as {status}."
    except IndexError:
        return "Error: Invalid todo index."