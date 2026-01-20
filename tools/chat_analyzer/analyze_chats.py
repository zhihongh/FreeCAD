import json
import os
import argparse
import sys
from datetime import datetime
from typing import List, Dict, Any

try:
    import openai
    from dotenv import load_dotenv
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

def setup_openai():
    """Setup OpenAI API key from environment variables."""
    if not HAS_OPENAI:
        print("Error: 'openai' and 'python-dotenv' packages are required for AI summarization.")
        print("Please install them using: pip install -r requirements.txt")
        return False
    
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        print("Warning: OPENAI_API_KEY not found in environment variables.")
        print("AI summarization will be skipped. Only text extraction will be performed.")
        return False
    
    return True

def extract_messages(conversation: Dict[str, Any]) -> str:
    """Extract text messages from a conversation object (ChatGPT format)."""
    text_content = []
    mapping = conversation.get("mapping", {})
    
    # Traverse the mapping to get messages in order
    # This is a simplified traversal, assuming linear conversation or taking the last leaf
    # For a proper export, we might need to handle branches, but usually current_node is the leaf
    
    current_node = conversation.get("current_node")
    
    while current_node:
        node = mapping.get(current_node)
        if not node:
            break
            
        message = node.get("message")
        if message:
            author = message.get("author", {}).get("role", "unknown")
            content = message.get("content", {})
            parts = content.get("parts", [])
            
            if parts and isinstance(parts[0], str) and len(parts[0]) > 0:
                text = "".join([str(p) for p in parts if p])
                text_content.append(f"**{author}**: {text}")
        
        current_node = node.get("parent")
        
    return "\n\n".join(reversed(text_content))

def summarize_chat(text: str) -> Dict[str, str]:
    """
    Summarize the chat content using OpenAI API.
    Returns a dictionary with 'summary' and 'category'.
    """
    if not os.getenv("OPENAI_API_KEY"):
        return {"summary": "AI summarization skipped (no API key).", "category": "Uncategorized"}

    try:
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes chat logs and categorizes them."},
                {"role": "user", "content": f"Please provide a concise summary (max 3 sentences) and a category (1-2 words) for the following chat conversation:\n\n{text[:3000]}..."} # Truncate to avoid token limits for this example
            ],
            temperature=0.5,
        )
        
        content = response.choices[0].message.content
        # Naive parsing - expecting the model to follow instructions roughly
        # Ideally we'd ask for JSON output
        
        return {
            "summary": content,
            "category": "AI Processed"
        }
    except Exception as e:
        print(f"Error during API call: {e}")
        return {"summary": "Error generating summary.", "category": "Error"}

def process_file(input_file: str, output_dir: str, use_ai: bool = False):
    """Process the exported conversations.json file."""
    
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found.")
        return

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"Reading {input_file}...")
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError:
        print("Error: Invalid JSON file.")
        return

    if not isinstance(data, list):
        print("Error: Expected a list of conversations.")
        return

    print(f"Found {len(data)} conversations. Processing...")

    for i, conv in enumerate(data):
        title = conv.get("title", f"conversation_{i}")
        create_time = conv.get("create_time", 0)
        date_str = datetime.fromtimestamp(create_time).strftime('%Y-%m-%d')
        
        # Sanitize filename
        safe_title = "".join([c for c in title if c.isalnum() or c in (' ', '-', '_')]).strip()
        safe_title = safe_title.replace(" ", "_")
        filename = f"{date_str}_{safe_title}.md"
        
        full_text = extract_messages(conv)
        
        if not full_text:
            continue

        summary_info = {"summary": "No summary generated.", "category": "Uncategorized"}
        if use_ai:
            summary_info = summarize_chat(full_text)
            
        # Write Markdown file
        output_path = os.path.join(output_dir, filename)
        with open(output_path, 'w', encoding='utf-8') as out:
            out.write(f"# {title}\n\n")
            out.write(f"**Date:** {date_str}\n")
            out.write(f"**Category:** {summary_info['category']}\n\n")
            out.write(f"## Summary\n{summary_info['summary']}\n\n")
            out.write(f"## Full Transcript\n\n{full_text}\n")
            
        if (i + 1) % 10 == 0:
            print(f"Processed {i + 1}/{len(data)} conversations...")

    print("Done!")

def main():
    parser = argparse.ArgumentParser(description="Analyze and summarize ChatGPT/Grok export files.")
    parser.add_argument("input_file", help="Path to conversations.json")
    parser.add_argument("--output-dir", "-o", default="analyzed_chats", help="Directory to save summaries")
    parser.add_argument("--ai", action="store_true", help="Use OpenAI to summarize and categorize (requires API Key)")
    
    args = parser.parse_args()
    
    use_ai = False
    if args.ai:
        use_ai = setup_openai()
        
    process_file(args.input_file, args.output_dir, use_ai)

if __name__ == "__main__":
    main()
