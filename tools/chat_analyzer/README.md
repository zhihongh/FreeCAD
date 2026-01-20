# Chat Export Analyzer

This tool helps you process and organize your chat history from services like ChatGPT (and potentially Grok, if the JSON format matches). It extracts conversations, optionally summarizes and categorizes them using OpenAI, and saves them as Markdown files.

## Features

- Parses `conversations.json` (standard ChatGPT export format).
- Extracts full conversation transcripts.
- (Optional) AI-powered summarization and categorization using OpenAI GPT model.
- Outputs clean Markdown files ready for reading or indexing.

## Setup

1.  **Install Dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

2.  **API Key (Optional):**
    If you want to use the AI summarization feature, you need an OpenAI API key.
    Create a `.env` file in this directory or export the variable:

    ```bash
    export OPENAI_API_KEY="your-api-key-here"
    ```

## Usage

1.  **Download your Data:**
    - **ChatGPT:** Go to Settings > Data Controls > Export Data. You will receive a zip file. Extract it and find `conversations.json`.

2.  **Run the Analyzer:**

    ```bash
    python analyze_chats.py /path/to/conversations.json --output-dir my_chat_summaries --ai
    ```

    - `--ai`: Enable AI summarization (requires API key). Omit this flag for simple text extraction.
    - `--output-dir`: Where to save the Markdown files (default: `analyzed_chats`).

3.  **Use in "Ask" Mode / Conversation:**
    - **In Cursor:** Reference the output folder (e.g., `@my_chat_summaries`) to ask questions about your past conversations.
    - **On Mobile:** You can access these Markdown summaries to have a conversation with your data on your phone using any LLM interface that supports file context.
