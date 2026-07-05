# WEEK5

## Having my-skill/ folder
And making all the documenttions be linked to a short table in the starting eith oly title nd link to the material for quick refernce without needing to go for the reading of the whole documentation.  reference by ids.

![image](./images/i1.png)



Example: Loading a PDF processing skill
Here's how Claude loads and uses a PDF processing skill:
Startup: System prompt includes: PDF Processing - Extract text and tables from PDF files, fill forms, merge documents
User request: "Extract the text from this PDF and summarize it"
Claude invokes: bash: read pdf-skill/SKILL.md → Instructions loaded into context
Claude determines: Form filling is not needed, so FORMS.md is not read
Claude executes: Uses instructions from SKILL.md to complete the task


The diagram shows:

Default state with system prompt and skill metadata pre-loaded
Claude triggers the skill by reading SKILL.md via bash
Claude optionally reads additional bundled files like FORMS.md as needed
Claude proceeds with the task


Extra features: 
Invocation control: disable-model-invocation (only you can trigger it, e.g. /deploy — you don't want the model deciding to deploy) vs. user-invocable: false (only the model, for background knowledge).
Arguments: /fix-issue 123 substitutes 123 into the body via a $ARGUMENTS placeholder.
Dynamic context: a !`git diff HEAD` line in the body runs before the model sees it, so the skill arrives with live data already inlined.
allowed-tools: pre-approving specific tools while a skill is active, so it doesn't re-prompt.
Running in a subagent (context: fork): the skill body becomes a fresh subagent's whole task — the exact Explore-subagent pattern from Week 4 Lesson 5.
 ![alt text]({BE2320FB-68F6-4F92-8341-0982A6EB43F6}.png)

 ![alt text]({CB7B3FBF-8B23-46F7-8356-4D5A87AE2738}.png)
 ![alt text]({41B11DEF-E083-4383-A98A-222C28DEEE9B}.png)

 https://code.claude.com/docs/en/skills#control-who-invokes-a-skill


Background jobs:

 🚀 New Features ImplementedInterrupt-to-Background (Ctrl+C): You no longer have to stare at a frozen terminal during long npm install or pytest runs. You can interrupt a running command and seamlessly push it to the background without killing the process.Daemon Job Monitoring: A silent background thread continuously watches your async jobs and captures their output the moment they finish.Agent Polling: The LLM is now aware of background tasks. It can check their status using the check_background_job tool and move on to other todo items while it waits.Notification System: High-level progress (like marking a todo complete or finishing a prompt) is logged to a centralized .agent/notifications.log file, keeping the terminal clean.CLI Notification Bar: You can type /notifs in your REPL at any time to see the last 5 major updates from the agent.🔄 The Code Flow: How It Works End-to-EndExecution Request: The agent decides to run a command and calls run_command.  Safety & Classification: exec.py intercepts this. It checks if it's destructive (asking for y/n) and if it's a known slow command (like pytest).  The Intercept (The Magic): If the command is slow, exec.py starts it and waits. If you hit Ctrl+C because it's taking too long, it catches the KeyboardInterrupt. It prompts you to push it to the background.  Asynchronous Handoff: If you press b, the process is saved to BACKGROUND_JOBS with a unique Job ID, and control is instantly returned to the agent with a message to check back later.  Silent Monitoring: The daemon thread (_job_monitor) in exec.py continuously polls running jobs. When one finishes, it saves the exit code and logs.  Task Completion & Logging: The agent checks the job using check_background_job. Once verified, it calls mark_todo(..., status="completed"). Inside plan.py, this triggers log_notification(), writing a clean success message to .agent/notifications.log.User Visibility: You type /notifs in the REPL. agent.py reads the log file and prints the latest updates so you know exactly what the agent achieved while you weren't looking


tui updated with the notif thingy
 Key Additions Made:Added Imports: Included os and the necessary Textual screen/container widgets (ModalScreen, Container) at the top of the file.  The NotificationModal Class: Inserted a new class defining the floating window, styled to display directly in the middle of the screen over the chat interface. It reads up to the last 15 lines from the .agent/notifications.log file.  New Binding: Added "ctrl+n" to the BINDINGS list in TUIAgent so the hotkey hint appears dynamically in the footer.  Action Method: Defined action_show_notifications(self) at the bottom of the TUIAgent class to trigger the push_screen logic whenever Ctrl+N is pressed. 