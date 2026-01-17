# TaskAgent: Your Personal ADHD-Friendly Assistant

This directory contains tools to help automate task management, specifically designed to bridge **Notion** and **Obsidian**, while adding an AI layer to help with executive dysfunction (ADHD).

## Why simple code?

You don't need a complex autonomous agent like Manus for this. A targeted script is:
1.  **Cheaper**: You pay only for your API usage (OpenAI/Notion).
2.  **Private**: Data runs locally on your machine.
3.  **Customizable**: You can tweak the "Encouragement" prompts to fit your exact mood needs.

## Tools Included

### 1. `adhd_agent.py` (New!)
A demonstration script that shows the full workflow you requested:
*   **Fetches Tasks**: Simulates getting "Today's Tasks" from Notion.
*   **AI Breakdown**: Uses an LLM (mocked) to split big tasks into 5-15 minute micro-steps.
*   **Time Boxing**: Estimates time for each step.
*   **Emotional Support**: Provides encouraging commentary to lower the "wall of awful".
*   **Obsidian Sync**: Generates a Markdown checklist ready for your Vault.

#### Usage:
```bash
python adhd_agent.py
```

### 2. `task_manager.py` & `obsidian_parser.py`
Earlier prototypes for parsing local Obsidian files and executing shell commands.

## How to make it "Real"

To turn `adhd_agent.py` into a production tool, you just need to swap the "Mock" classes with real API calls.

### Step 1: Install Dependencies
```bash
pip install notion-client openai
```

### Step 2: Notion API (`MockNotionClient` -> Real)
```python
from notion_client import Client

class RealNotionClient:
    def __init__(self, token, database_id):
        self.notion = Client(auth=token)
        self.db_id = database_id

    def get_todays_tasks(self):
        # Query database for items where Date is Today and Status is To Do
        response = self.notion.databases.query(
            **{
                "database_id": self.db_id,
                "filter": {
                    "property": "Date",
                    "date": {"equals": datetime.now().date().isoformat()}
                }
            }
        )
        return [{"title": r['properties']['Name']['title'][0]['plain_text']} for r in response['results']]
```

### Step 3: OpenAI API (`MockLLM` -> Real)
```python
from openai import OpenAI

class RealLLM:
    def __init__(self, key):
        self.client = OpenAI(api_key=key)

    def generate_breakdown(self, task):
        prompt = f"""
        Act as a supportive ADHD coach. 
        Break down the task "{task}" into tiny, non-intimidating steps (max 15 mins each).
        Add a warm, encouraging remark.
        Format as JSON.
        """
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        # Parse JSON from response...
```
