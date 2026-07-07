# ClankerBot 

# Project Overview

Transformed Code Scout from a rigid, hardcoded script into a modular, extensible artificial intelligence platform. The system acts as an agent that actively reasons about the environment rather than operating as a black box. The platform solves blind overconfidence by switching personas to aggressively critique generated work, ensuring secure and reliable code execution.

# Architecture

The architecture relies on decoupled logic and external server integrations to function as a seamless pipeline. 

*   **Skills Engine:** A directory based system where each skill is a folder containing markdown files with YAML frontmatter.
*   **Config System:** A JSON configuration file that acts as a blueprint, decoupling logic from data and allowing environment specific configurations.
*   **Model Context Protocol Bridge:** The connective tissue that manages the lifecycles of subprocesses, establishes secure standard input and output connections, and routes tool requests to the appropriate server.
*   **Background Jobs:** An asynchronous daemon thread that continuously watches asynchronous jobs, captures output, and logs progress without interrupting the main workflow.
*   **Saving and Memory:** A dedicated directory for storing conversation history as clean Markdown files, automatically extracting context and external data sources.

# Features and Commands

| Feature | Command | Description |
| :--- | :--- | :--- |
| **System Status** | `/status` | Displays the active session, connected servers, and currently loaded skills. |
| **Textual Interface** | `/tui` | Boots a rich terminal based user interface with seamless context switching. |
| **Active Memory Export** | `/save1` | Exports the current active memory to a clean Markdown file. |
| **Complete History Export** | `/save2` | Retrieves and exports the complete conversation history from disk. |
| **Session List** | `/sessions` | Lists all past and available sessions with generated titles. |
| **Resume Session** | `/resume [id]` | Hot swaps the current context to a previous conversation state. |
| **Delete Session** | `/delete [id]` | Permanently wipes a session from disk and spawns a fresh environment. |
| **Background Alerts** | `/notifs` | Pulls up the most recent background task completions. |
| **Post Mortem Review** | `/postmortem` | Forces the agent to analyze the session history and generate an honest critique. |

---

### Feature Deep Dive

#### 1. UI Switching (`/tui`)
The `/tui` command provides an alternative, high-density visualization of agent activity. When triggered, the system initiates a terminal-based user interface that renders a multi-pane environment.
*   **Context Preservation:** The transition is seamless; the session state, message history, and current configuration are passed directly from the standard REPL to the TUI.
*   **Bidirectional Movement:** The interface allows for switching back to the standard REPL via internal commands without losing the session, enabling the use of a rich interface for complex tasks and a simple command-line interface for quick interactions.

#### 2. Memory Management (`/save1` and `/save2`)
These commands allow for the structured offloading of intelligence from volatile memory to persistent storage. All captured knowledge is stored in a format that remains accessible and understandable for long-term review.
*   **Active Memory Export (`/save1`):** Captures the current, immediate session context. This is designed for researchers who want to snapshot the conversation mid-flow before shifting topics.
*   **Complete History Export (`/save2`):** Retrieves the full conversation history from the local JSON session file. This provides a comprehensive audit trail of the entire task lifecycle.
*   **Markdown Formatting:** All saved session histories are converted from raw, machine-readable JSON into clean, structured Markdown documents.
*   **Directory Organization:** These files are automatically organized and stored within the `notes/` directory, ensuring a centralized location for all research snapshots.
*   **Intelligent Extraction:** Both commands strip out raw JSON, system logs, and internal tool metadata. They automatically parse the history to compile a dedicated "Sources & Context Gathered" section, identifying which files, web searches, or tools were utilized to reach conclusions.

#### 3. Live Narration Mode
This feature provides real-time transparency during tool execution. 
*   **Mechanism:** Before the agent invokes any tool, the system intercepts the intent and maps the tool name and arguments to a plain-English rationale.
*   **Visual Logic:** By utilizing terminal control codes (`\r` and `\033[2K`), the system clears the "Agent is thinking..." spinner and replaces it with a persistent, human-readable thought trace. This ensures that every automated action is preceded by a clear, visible justification.

#### 4. On-Demand Post-Mortems (`/postmortem`)
This feature implements automated metacognition.
*   **Analytical Loop:** When invoked, the system bypasses the standard interaction loop and injects the entire conversation history into a highly analytical prompt.
*   **Output:** The agent generates a structured Markdown document covering the goal, failed strategies, successful approaches, and future recommendations. This file is saved to the `notes/` directory, providing an immediate, high-quality summary for documentation or final submissions.

#### 5. Adversarial Self-Review (Devil's Advocate)
This feature introduces a dynamic, persona-based security and logic audit.
*   **Adversarial Persona:** Upon loading the `devils_advocate` skill, the agent enters a high-cynicism mode where it is explicitly instructed to ignore social constraints and focus entirely on identifying potential failure points.
*   **Attack Vectors:** The agent evaluates generated code against specific security and stability criteria: path traversal risks, injection flaws, concurrency issues, and unhandled edge cases.
*   **Outcome:** Rather than attempting to "fix" the output, the agent produces a raw, bulleted list of critical flaws, edge cases, and a final verdict on whether the code is safe to deploy.

### 6. Spinner and Live Narration
These features provide real-time transparency and feedback, ensuring the system state is always visible to the user.

*   **Spinner Animation:** A background thread dynamically overwrites the terminal line with a rotating spinner character. This provides instant visual confirmation that the agent is actively processing requests, eliminating uncertainty regarding system responsiveness.
*   **Live Narration Mode:** Before invoking a tool, the agent intercepts the intent and maps the action to a human-readable English sentence. The system uses terminal control codes to instantly erase the spinner line and replace it with a persistent, cyan-colored "Agent Thought" rationale. 
*   **TUI Integration:** In the Textual User Interface, tool executions are routed to a dedicated, high-density log panel on the right side of the screen. This ensures that background actions remain visible without cluttering the main interaction flow.
*   **Professional Feedback:** The cascading effect—where the spinner vanishes and the rationale prints before a tool executes—proves that the agent is actively reasoning about the environment rather than operating as an opaque black box.

### 7. MCP Integration and Component Pipeline

The system utilizes three primary components to bridge the gap between the LLM and external data sources like the GitHub API.

*   **Configuration (`config.json`):** This file acts as the system blueprint. It defines which MCP servers exist, specifies the commands used to boot them, and outlines the required environment variables for each connection. When the agent boots, it reads this file, locates the `mcp_servers` entry, and launches the server as a subprocess.
*   **The Server (`github_mcp.py`):** This acts as an independent FastMCP server. It validates the `GITHUB_PERSONAL_ACCESS_TOKEN` environment variable upon startup to ensure secure authentication. The server uses the `@mcp.tool()` decorator to register Python functions—such as `list_my_repos`—as compliant tools, automatically converting docstrings into JSON schemas that the LLM can interpret. It maintains a continuous loop listening for requests over standard input/output.
*   **The Bridge (`mcp_bridge.py`):** This module serves as the connective tissue for the architecture.
    *   **Lifecycle Management:** It utilizes an `AsyncExitStack` to manage the subprocess lifecycles defined in the configuration, ensuring sessions remain alive while the agent is active.
    *   **Tool Discovery:** It queries the server for available tools and translates them into the native OpenAI JSON function-calling schema, which are then injected into the agent's tool list.
    *   **Request Routing (`call_tool`):** When the LLM decides to trigger a tool, `agent.py` passes the request to this bridge. The bridge asks the MCP session to execute the requested tool and formats the resulting payload back into a text string that the LLM can process.

### 8. tried to make a website out this but it is still working
* it would have shown the architecture of the project in read only form all the tools listed in one pop up with hyper links connecting to the 
actual file location and it would have its connected terminal and the tui, but thi s task would later be completed when i have more time as it had to tackle some permissio issues
  

---

Made under the guidance of ARIES club IITD [guidance](https://github.com/ishananand06/CSOT26_GenAI-Agentic.git)

This will be the main project doc-

Week1's Sumission Doc: [Week 1 Submission](week_1/SUBMISSION.md)

Week2's Submission Doc: [Week 2 Submission](week_2/SUBMISSION.md)

Week3's Submission Doc: [Week 3 Submission](week_3/SUBMISSION.md)

Week4's Submission Doc: [Week 4 Submission](week_4/SUBMISSION.md)

Week5's Submission Doc: [Week 5 Submission](week_5/SUBMISSION.md)

