"""
Build 3: Todo Tools
======================
A persistent, JSON-backed todo list the model maintains itself.
Enforces evidence-based verification for completed tasks.
"""

import os
import json
import uuid

WORKSPACE_ROOT = os.path.abspath(os.environ.get("WORKSPACE_ROOT", "."))
TODO_FILE = os.path.join(WORKSPACE_ROOT, ".agent_todos.json")

VALID_STATUSES = {"pending", "in_progress", "completed", "blocked", "error"}





def _load_todos() -> list:
    """Helper: Load todos from disk."""
    if not os.path.exists(TODO_FILE):
        return []
    try:
        with open(TODO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

def _save_todos(todos: list):
    """Helper: Save todos to disk."""
    with open(TODO_FILE, "w", encoding="utf-8") as f:
        json.dump(todos, f, indent=2)


def add_todos(items: list[dict]) -> dict:
    """
    Add one or more todos to the list.
    Expected dict format: {"title": str, "description": str, "verification_method": str}
    """
    todos = _load_todos()
    added_ids = []
    
    for item in items:
        # Require essential fields
        if not all(k in item for k in ("title", "description", "verification_method")):
            return {"error": "All items must include 'title', 'description', and 'verification_method'."}
            
        new_todo = {
            "id": str(uuid.uuid4())[:8],  # Short UUID for ease of use
            "title": item["title"],
            "description": item["description"],
            "verification_method": item["verification_method"],
            "status": "pending",
            "remark": ""
        }
        todos.append(new_todo)
        added_ids.append(new_todo["id"])
        
    _save_todos(todos)
    return {"message": f"Successfully added {len(added_ids)} todos.", "added_ids": added_ids, "current_list": todos}


def get_todos(status_filter: str = None) -> dict:
    """Return the current list, optionally filtered by status."""
    todos = _load_todos()
    if status_filter:
        if status_filter not in VALID_STATUSES:
            return {"error": f"Invalid status filter. Must be one of {VALID_STATUSES}"}
        todos = [t for t in todos if t["status"] == status_filter]
        
    return {"todos": todos, "total": len(todos)}


def mark_todo(todo_id: str, status: str, remark: str = "") -> dict:
    """
    Update a todo's status. 
    Strictly requires a `remark` (evidence) if marking as completed, blocked, or error.
    """
    if status not in VALID_STATUSES:
        return {"error": f"Invalid status '{status}'. Must be one of {VALID_STATUSES}"}
        
    if status in {"completed", "blocked", "error"} and len(remark.strip()) < 5:
        return {
            "error": (
                f"Cannot transition to '{status}' without a valid remark. "
                "Provide concrete evidence (e.g., 'Exit code 0', 'Tests passed') "
                "or explain why it is blocked/errored."
            )
        }

    todos = _load_todos()
    for todo in todos:
        if todo["id"] == todo_id:
            todo["status"] = status
            todo["remark"] = remark
            _save_todos(todos)
            return {"message": f"Todo {todo_id} updated to {status}.", "todo": todo}
            
    return {"error": f"Todo with ID '{todo_id}' not found."}


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "add_todos",
            "description": (
                "Add tasks to your persistent execution plan. "
                "Call this before starting multi-step work to articulate your sub-goals. "
                "You must define how you will verify each item is complete."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string", "description": "Short summary of the task."},
                                "description": {"type": "string", "description": "Specific details of what needs to be done."},
                                "verification_method": {
                                    "type": "string", 
                                    "description": "Concrete way to prove it worked (e.g., 'run pytest and confirm exit code 0')."
                                }
                            },
                            "required": ["title", "description", "verification_method"]
                        }
                    }
                },
                "required": ["items"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_todos",
            "description": "Retrieve your current task list to review your progress.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status_filter": {
                        "type": "string",
                        "enum": list(VALID_STATUSES),
                        "description": "Optional. Filter by pending, in_progress, completed, blocked, or error."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "mark_todo",
            "description": (
                "Update the status of a specific task by its ID. "
                "CRITICAL: If marking a task 'completed', you MUST provide a 'remark' detailing "
                "the evidence (e.g., 'Ran tests, exit code 0'). Claims of completion without evidence will be rejected."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "todo_id": {"type": "string", "description": "The ID of the task to update."},
                    "status": {
                        "type": "string",
                        "enum": list(VALID_STATUSES),
                        "description": "The new status of the task."
                    },
                    "remark": {
                        "type": "string",
                        "description": "Evidence of completion, reason for block, or error details. Required for completed/blocked/error statuses."
                    }
                },
                "required": ["todo_id", "status"]
            }
        }
    }
]


if __name__ == "__main__":
    # Clean up any existing test file
    if os.path.exists(TODO_FILE):
        os.remove(TODO_FILE)

    print("1. Adding initial todos...")
    add_result = add_todos([
        {
            "title": "Fix Auth Bug",
            "description": "Resolve the JWT token expiration logic.",
            "verification_method": "Run pytest tests/test_auth.py and confirm exit code 0."
        },
        {
            "title": "Update DB Schema",
            "description": "Add the last_login column to users table.",
            "verification_method": "Run migration script and check DB schema dump."
        }
    ])
    print(json.dumps(add_result,indent=2))
    print("-" * 40)

    task_id = add_result["added_ids"][0]

    print(f"2. Marking task {task_id} as 'in_progress'...")
    print(mark_todo(task_id, "in_progress", "Started investigating the token logic."))
    print("-" * 40)

    print(f"3. Attempting to mark task {task_id} as 'completed' WITHOUT evidence...")
    # This should fail and return an error because remark is empty/missing
    fail_result = mark_todo(task_id, "completed")
    print(json.dumps(fail_result,indent=2))
    print("-" * 40)

    print(f"4. Marking task {task_id} as 'completed' WITH proper evidence...")
    # This should succeed
    success_result = mark_todo(task_id, "completed", "Ran pytest tests/test_auth.py. Exit code 0, 15 tests passed.")
    print(json.dumps(success_result,indent=2))
    print("-" * 40)

    print("5. Current Todo List State:")
    print(json.dumps(get_todos()["todos"], indent=2))