## Setup requirements:
1.  - pip install textual openai requests python-dotenv
2.  - **configure api keys**:
    a `.env` file in the project root with api keys:
    ```text
    OPENROUTER_API_KEY=your_openrouter_key_here
    SERPER_API_KEY=your_serper_key_here
    ```

--- 

## WorkFlow
1. **personality engine**: I made it to give answer while also having a mild sarcastic personality to not bore me**.
2. **tui interface**: uses a dual panel layout via `textual`:
   - **conversation log**: tracks your chat and the agent's replies.
   - **tool execution trace**: displays exactly what tools the agent is calling and the results it fetches.

3. **autonomous loop**: if the agent needs data to answer me it will automatically trigger a tool, process the result, and present the final answer to while writing its process in the side panel.

---

## features(thing which needed to be take care as it lead to a lot of error i couldnt fix in time.)
* **streaming, compacting**: couldnt able to implement as it was leading to crashed and error.
* **error handling**: if a website blocks the agent (e.g., 403 forbidden) or a tool fails, it logs the error clearly in the trace panel instead of freezing. This was also a problem.
* **robust tools**:
    * `web_search`: fetches live data using serper.
    * `web_fetch`: grabs raw content from websites (bypassing basic blocks).
    * `save_research_note`: stores the findings into markdown files in a local `/notes` folder.
* **token usage**: had a major issue of the tokens being used , so i have to reduce it to max_tokens=2000

## controls

* **input**: type your query in the bottom input box and hit **enter**.
* **scroll**: use your mouse wheel or trackpad. the panels support horizontal scrolling if lines are long.
* **quit**: press `ctrl+q` in the terminal to stop the agent.

---

### IMplementation

The workflow follows a **synchronous-recursive loop** managed within a dedicated thread. Here is the step-by-step breakdown:

1.  **User Input Submission**: The `on_input_submitted` method captures the user's text, appends it to `self.history`, and triggers `run_agent_loop()` inside a background thread (using Textual's `@work` decorator).

2.  **LLM Inference**: The `run_agent_loop` sends the entire `self.history` list to the LLM via OpenRouter. We set `stream=False` to ensure the entire message is captured in one go, avoiding UI crashes.

3.  **UI Update (Chat)**: If the LLM generates a text response (`msg.content`), the main thread is signaled via `self.app.call_from_thread` to update the **CONVERSATION LOG** panel.

4.  **Tool Dispatcher**: If the LLM identifies that a tool is required, it returns a `tool_calls` object. The loop iterates through these calls:

    *   **Trace Update (Pre-Execution)**: The `tool-log` is updated to show which tool is being attempted.
    *   **Execution**: The specific function (e.g., `web_search`) is executed.
    *   **Trace Update (Post-Execution)**: The result of the tool is written to the `tool-log`.
    *   **History Update**: The tool's output is appended to `self.history` as a `role: tool` message.

5.  **Recursion**: The loop calls `self.run_agent_loop()` again. This is critical: it feeds the **tool output** back into the LLM, allowing it to synthesize a final answer based on the search results it just retrieved.

6.  **Error Handling**: Every stage is wrapped in a `try/except` block, ensuring that if a network error occurs or an invalid tool call is made, the app logs the error to the UI rather than crashing the entire process.
