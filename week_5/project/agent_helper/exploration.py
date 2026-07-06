import json
from tools.files import read_file, list_files
from tools.search import grep, list_definitions, get_repo_map
from tools.plan import set_active_session
from agent_helper.sessions import build_system_prompt

def delegate_exploration(task_description: str) -> dict:
    # Local import to prevent circular dependency with agent.py
    from agent import Agent
    
    class ExploreAgent(Agent):
        def __init__(self, session_id=None):
            # We explicitly initialize the parent Agent with the temp scout ID
            super().__init__(session_id="temp_scout")
            self.session_title = "Scout"
            
            system_prompt = (
                "You are a Scout Subagent. Your job is to thoroughly explore the codebase to answer "
                "the orchestrator's question. Use grep, read_file, list_definitions, and get_repo_map. "
                "You CANNOT make changes. Return a dense, highly formatted digest."
            )
            self.messages = [{"role": "system", "content": system_prompt}]
            set_active_session(self.session_id, self.session_title)

        def dispatch(self, tool_call) -> str:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            read_only_tools = {
                "read_file": read_file, "list_files": list_files, "grep": grep,
                "list_definitions": list_definitions, "get_repo_map": get_repo_map
            }
            if name in read_only_tools:
                try:
                    return json.dumps(read_only_tools[name](**args))
                except Exception as e:
                    return json.dumps({"error": str(e)})
            return json.dumps({"error": f"Tool '{name}' is forbidden for the Scout Subagent."})

    print(f"\n\033[93m>> Dispatching Scout Subagent: {task_description[:50]}...\033[0m")
    scout = ExploreAgent()
    digest = scout.run_once(task_description)
    print(f"\033[93m<< Scout Subagent Returned.\033[0m\n")
    return {"scout_digest": digest}