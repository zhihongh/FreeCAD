import subprocess
import os
import sys

# Mock LLM Client
class LLMRefiner:
    def refine_task(self, task_content):
        """
        Simulates sending a task to an LLM to break it down.
        In a real scenario, this would call OpenAI/Anthropic API.
        """
        print(f"Thinking about: {task_content}...")
        
        # Simple heuristic for demo: split by 'and' or ','
        if " and " in task_content:
            subtasks = task_content.split(" and ")
            return [t.strip() for t in subtasks]
        
        return [task_content]

class TaskExecutor:
    def execute(self, task_content):
        """
        Executes a task. 
        If it looks like a shell command (starts with $ or run:), run it.
        Otherwise, just log it.
        """
        if task_content.startswith("$ ") or task_content.startswith("run: "):
            cmd = task_content.replace("$ ", "").replace("run: ", "")
            print(f"Executing shell command: {cmd}")
            try:
                result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
                print(f"Output: {result.stdout}")
                return True
            except subprocess.CalledProcessError as e:
                print(f"Error: {e.stderr}")
                return False
        else:
            print(f"Manual task (not executable code): {task_content}")
            # Here you could add more logic, e.g., create a file, etc.
            return True

def main():
    # Example usage
    if len(sys.argv) < 3:
        print("Usage: python task_manager.py <vault_path> <note_filename>")
        print("Example: python task_manager.py ./my_vault todo.md")
        return

    vault_path = sys.argv[1]
    note_filename = sys.argv[2]

    # Import here to avoid circular dependency if expanded
    try:
        from obsidian_parser import ObsidianParser
    except ImportError:
        # If running as script
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from obsidian_parser import ObsidianParser

    parser = ObsidianParser(vault_path)
    refiner = LLMRefiner()
    executor = TaskExecutor()

    print(f"Scanning {note_filename} in {vault_path}...")
    tasks = parser.find_tasks(note_filename)
    
    if not tasks:
        print("No pending tasks found.")
        return

    print(f"Found {len(tasks)} tasks.")

    for task in tasks:
        print(f"\nProcessing: {task['content']}")
        
        # 1. Refine
        subtasks = refiner.refine_task(task['content'])
        if len(subtasks) > 1:
            print(f"-> Broken down into {len(subtasks)} subtasks:")
            for st in subtasks:
                print(f"   - {st}")
        
        # 2. Execute (each subtask)
        all_success = True
        for st in subtasks:
            success = executor.execute(st)
            if not success:
                all_success = False
        
        # 3. Update status
        if all_success:
            parser.mark_task_complete(task)

if __name__ == "__main__":
    main()
