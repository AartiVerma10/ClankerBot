# -WEEk4-

## Theory:

When an agent has been given a task to verify if it really did the work there can be four types of strictness for checking:
- 1. In one prompt: EXplicitly telling it in tge prompt to check whether its answer is correct and do not reply the final ans until all its fixes are correct.
- 2. goal comdition - to set a background rule , As the AI works turn-by-turn, an automated evaluator constantly checks that goal. The AI is literally not allowed to declare the task finished until that background goal is met.
- 3. another ai: check one ai models reply through an another ai model.
- 4. hook: This is a hard-coded programmatic block. A "hook" is a script that runs automatically when a specific event happens. Here, when the AI tries to execute a "Stop" command, your script runs a real test (like npm test). If the test fails, the AI is blocked from stopping and forced to try again. (The text notes it will force-stop after 8 failed attempts so the AI doesn't get stuck in an infinite loop).

Recommended workflow:
- 1. Explore: Tell the agent the problem statement let it read thr required field of files without editing anything.
- 2. Plan:  Ask it how will it do the required task, and its workflow. And have it in a text editor.
- 3. Implement: Letting it implement.
- 4. Commit:  Asking it the commit the changes with a description.

## Built1:

