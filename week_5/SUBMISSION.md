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

---

# Transitioning from Week 4 to Week 5

### Skills and Protocol Integrations
Moved away from bloated system prompts by implementing a dynamic skills engine. The system now uses a tool to inject procedure instructions into active memory only when needed, allowing for zero code extensibility. Connected a local Model Context Protocol bridge to communicate with external APIs, querying for available tools and mapping them to native function calling schemas.

### Problems Faced and Recoveries
Implementing the local bridge required strict adherence to asynchronous task management, leading to several architectural hurdles:

*   **Async Context Mismatch:** The run loop was synchronous but used asynchronous commands to open long lived server connections, causing runtime errors. Refactored the entire agent structure to be fully asynchronous.
*   **Missing Execution Logic:** The agent apologized instead of executing commands because the manager was missing routing logic. Added a specific method to forward arguments to the session and parse the responses.
*   **Bad Credentials:** The configuration file incorrectly hardcoded a string as an access token. Removed the hardcoded string, generated new credentials, and placed them securely in an environment file.
*   **Graceful Shutdown Failure:** Quitting the application broke the loop but left execution stacks dangling. Added a close method at the end of the run sequence to cleanly terminate all streams.

