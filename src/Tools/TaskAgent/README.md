# Task Agent: Notion/Obsidian Automation

This tool demonstrates how to refine and automatically execute tasks from Obsidian (and conceptually Notion).

## How it works

1.  **Read**: Scans a Markdown file (Obsidian vault) for tasks defined as `- [ ]`.
2.  **Refine**: Uses a logic layer (mock LLM) to break down complex tasks.
3.  **Execute**: Runs tasks that are marked as commands (e.g., starting with `$` or `run:`).
4.  **Update**: Marks the task as complete `[x]` in the original file.

## Usage

1.  Create a "vault" directory and a markdown file (e.g., `tasks.md`) with some tasks:
    ```markdown
    - [ ] Print hello world via command line
    - [ ] run: echo "Hello World"
    - [ ] $ ls -la
    ```

2.  Run the script:
    ```bash
    python task_manager.py /path/to/vault tasks.md
    ```

## Extending to Notion

To support Notion:
1.  Install `notion-client`: `pip install notion-client`
2.  Create an integration in Notion and get the API Key.
3.  Share your database with the integration.
4.  Implement a `NotionParser` class similar to `ObsidianParser` that queries the Notion API for pages/blocks with "To Do" status.

## Extending with Real LLM

To use a real LLM for refinement:
1.  Install an SDK (e.g., `openai` or `anthropic`).
2.  Update `LLMRefiner.refine_task` to send the prompt to the API and parse the response.

## Example

```python
# In task_manager.py
class LLMRefiner:
    def refine_task(self, task_content):
        # Call GPT-4 here
        # prompt = f"Break down this task into executable steps: {task_content}"
        # response = client.chat.completions.create(...)
        # return parse_steps(response)
```
