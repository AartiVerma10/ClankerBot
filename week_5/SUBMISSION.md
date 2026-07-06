# Week 5: Code Scout Project Documentation

![New Architecture]({9D1F3EB2-A658-4B92-B7C9-5A06DD818220}.png)

I have transformed Code Scout from a rigid, hardcoded script into a modular, extensible AI platform. This document outlines the architecture, the specific features implemented, and the engineering problems solved[cite: 9].

## Architecture Overview

| ID | Title | Reference |
| :--- | :--- | :--- |
| 1 | Skills Engine | skills/ directory |
| 2 | Config System | config.json |
| 3 | MCP Bridge | mcp_bridge.py |
| 4 | UI/TUI Updates | tui.py |
| 5 | Background Jobs | exec.py |
| 6 | Saving/Memory | notes/ directory |

## Core Modules

### 1. Skills Engine
I implemented a directory based system for skills. Each skill is a folder containing a SKILL.md file with YAML frontmatter. I use a load_skill tool to dynamically inject procedure instructions into my active memory when needed[cite: 9]. This approach solves system prompt bloat through progressive disclosure and allows for zero-code extensibility[cite: 2].

### 2. Configuration as Code
I moved tool registries and active skills into config.json. My agent now acts as an engine that reads this file at startup, decoupling logic from data[cite: 9]. This fixes hardcoding brittleness and allows for environment-specific configurations[cite: 2].

### 3. Model Context Protocol Integration
I implemented mcp_bridge.py to manage connections to MCP servers. It establishes secure connections via stdio, queries for tools, maps them to an OpenAI compatible schema, and routes commands via the dispatch method in agent.py[cite: 8]. This enables me to connect to any MCP-compliant server[cite: 2].

### 4. Background Job System
I implemented an asynchronous daemon thread in exec.py to monitor long running processes[cite: 9].
* Interrupt-to-Background: I can interrupt a running command and push it to the background without killing the process[cite: 9].
* Daemon Job Monitoring: A background thread continuously watches async jobs and captures output upon completion[cite: 9].
* Agent Polling: I am aware of background tasks and can check their status using check_background_job while working on other items[cite: 9].
* Notification System: Progress is logged to .agent/notifications.log. I can type /notifs in the REPL to view the latest updates[cite: 9].

## UI and Memory Management

### UI Enhancements
1. Tool Trace Panel: Backend tool executions route to a dedicated log on the right side of the TUI[cite: 9].
2. Thinking Indicator: I implemented a blinking text indicator to show processing status[cite: 9].
3. Notification Modal: Ctrl+N triggers a floating window displaying updates from notifications.log[cite: 9].
4. Toggleable Shortcuts: The H key toggles a hidden panel that lists keyboard bindings[cite: 9].
5. Tool Execution: I implemented the execution loop for web_search, web_fetch, and save_research_note[cite: 9].

### Memory and Session Management
1. Manual Memory (Ctrl+S/Ctrl+R): I save the current conversation as a Markdown file in the notes/ directory. Pressing Ctrl+R reads saved files and injects them into my memory as a background knowledge manifest[cite: 9].
2. Save Commands: I implemented /save1 to export active memory and /save2 to export the complete history from disk. These exports filter out raw system and tool data to maintain readability[cite: 9].
3. Bidirectional Switching: I enabled movement between the terminal and TUI using the /tui and /repl commands[cite: 9].
4. Session Deletion: I added a delete_session function and mapped it to /delete <id> in both the REPL and TUI[cite: 9].

### Tool Call Visualization
I added a spinner animation that dynamically overwrites the current terminal line with the name of the tool currently being executed. This provides real-time feedback without cluttering the console with logs[cite: 9].