import re
import os

class ObsidianParser:
    def __init__(self, vault_path):
        self.vault_path = vault_path

    def find_tasks(self, file_path):
        """
        Reads a markdown file and returns a list of tasks.
        """
        full_path = os.path.join(self.vault_path, file_path)
        if not os.path.exists(full_path):
            print(f"File not found: {full_path}")
            return []

        tasks = []
        with open(full_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for i, line in enumerate(lines):
                # Match unchecked tasks: - [ ] Task description
                match = re.match(r'^\s*-\s*\[ \]\s+(.*)', line)
                if match:
                    tasks.append({
                        'content': match.group(1).strip(),
                        'line': i + 1,
                        'file': file_path,
                        'status': 'pending'
                    })
        return tasks

    def mark_task_complete(self, task):
        """
        Marks a task as complete in the file: - [x]
        """
        full_path = os.path.join(self.vault_path, task['file'])
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            line_idx = task['line'] - 1
            if 0 <= line_idx < len(lines):
                lines[line_idx] = lines[line_idx].replace('[ ]', '[x]', 1)
                
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                print(f"Marked task as complete: {task['content']}")
                return True
        except Exception as e:
            print(f"Error marking task complete: {e}")
            return False
