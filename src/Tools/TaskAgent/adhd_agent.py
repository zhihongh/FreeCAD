import sys
import time
import random

# Mock classes to simulate external libraries (notion-client, openai)
class MockNotionClient:
    def get_todays_tasks(self):
        """
        Simulates fetching tasks from a Notion Database filter for 'Today'
        """
        # In a real scenario, this would use notion_client.Client to query a database
        print("🔍 Connecting to Notion... fetching 'Today's Tasks'...")
        time.sleep(1) 
        return [
            {"id": "1", "title": "Complete Project Report"},
            {"id": "2", "title": "Clean the garage"},
            {"id": "3", "title": "Learn Python basics"}
        ]

class MockLLM:
    def generate_breakdown(self, task_title):
        """
        Simulates an LLM breaking down a task into ADHD-friendly micro-steps
        with time estimates and emotional support.
        """
        print(f"🤖 Thinking about how to make '{task_title}' easier...")
        time.sleep(1.5)
        
        # Simple heuristic responses for demonstration
        if "Report" in task_title:
            return {
                "steps": [
                    {"step": "Open the document and write the title", "time": "2 mins"},
                    {"step": "Write 3 bullet points for the main sections", "time": "5 mins"},
                    {"step": "Fill in the first section (ugly draft mode)", "time": "15 mins"},
                    {"step": "Take a coffee break", "time": "5 mins"}
                ],
                "encouragement": "Reports are scary, but you only need to start with the title! You got this!"
            }
        elif "Clean" in task_title:
            return {
                "steps": [
                    {"step": "Put on your favorite music playlist", "time": "2 mins"},
                    {"step": "Pick up 5 pieces of obvious trash", "time": "5 mins"},
                    {"step": "Organize one specific shelf", "time": "10 mins"}
                ],
                "encouragement": "Don't look at the whole mess. Just 5 pieces of trash. Easy peasy!"
            }
        else:
            return {
                "steps": [
                    {"step": "Open the tutorial website", "time": "1 min"},
                    {"step": "Read the first paragraph", "time": "3 mins"},
                    {"step": "Write one line of code", "time": "5 mins"}
                ],
                "encouragement": "Learning is a journey. One line of code is infinitely better than zero!"
            }

    def chat(self, user_input, context):
        """
        Simulates a Q&A interaction
        """
        return f"That's a valid point! Let's adjust. (AI would reply to '{user_input}' here...)"

class ObsidianSync:
    def save_to_obsidian(self, task_title, breakdown_data, vault_path="./ObsidianVault"):
        """
        Saves the breakdown to a Markdown file in Obsidian
        """
        filename = f"{task_title.replace(' ', '_')}.md"
        content = f"# {task_title}\n\n"
        content += f"> 💡 **AI Note**: {breakdown_data['encouragement']}\n\n"
        content += "## Action Plan\n"
        
        total_minutes = 0
        for item in breakdown_data['steps']:
            content += f"- [ ] {item['step']} *({item['time']})*\n"
            # deeply simplified time parsing
            try:
                mins = int(item['time'].split()[0])
                total_minutes += mins
            except:
                pass
                
        content += f"\n---\n**Total estimated time:** {total_minutes} mins\n"
        
        # In real usage, write to file system
        # with open(os.path.join(vault_path, filename), 'w') as f: ...
        print(f"📝 Synced to Obsidian: [[{filename}]]")
        print("---------------------------------------------------")
        print(content)
        print("---------------------------------------------------")

def main():
    print("🌟 Welcome back! Let's handle today's tasks with zero stress.")
    
    # 1. Connect to Notion
    notion = MockNotionClient()
    tasks = notion.get_todays_tasks()
    
    print(f"\nFound {len(tasks)} tasks for today. Let's take them one by one.\n")
    
    llm = MockLLM()
    obsidian = ObsidianSync()
    
    for task in tasks:
        print(f"👉 Current Focus: **{task['title']}**")
        
        # Interactive Check
        user_ready = input("   Ready to break this down? (y/skip/edit): ").strip().lower()
        if user_ready == 'skip':
            continue
        elif user_ready == 'edit':
             new_title = input("   Rename task for clarity: ")
             task['title'] = new_title
        
        # 2. LLM Refinement
        breakdown = llm.generate_breakdown(task['title'])
        
        print(f"\n   ✨ AI Suggestion: {breakdown['encouragement']}")
        print("   Proposed Plan:")
        for i, step in enumerate(breakdown['steps']):
            print(f"     {i+1}. {step['step']} ({step['time']})")
            
        # 3. Interactive Adjustment (Q&A)
        while True:
            feedback = input("\n   Look good? (y) or ask changes (e.g., 'too long'): ").strip().lower()
            if feedback == 'y' or feedback == '':
                break
            else:
                response = llm.chat(feedback, task)
                print(f"   🤖 AI: {response}")
                print("   (Assuming adjustments made...)")
                break # Break for demo purposes
        
        # 4. Sync to Obsidian
        obsidian.save_to_obsidian(task['title'], breakdown)
        print("\n   ✅ Saved to Obsidian! You are set to go.\n")
        
    print("🎉 All tasks processed! Have a productive (and kind to yourself) day!")

if __name__ == "__main__":
    main()
